import airplane from "airplane"

// TODO: Change to Python when Python workflows are available
const NUM_TEARDOWN_ATTEMPTS = 3;
type AirplaneArgs = { [key: string]: any };
type DeprovInfo = {
	aws_account_id: string;
	deprovision_state: string;
	dns_removal_time: string;
	organization: string;
	region: string;
	teardown_attempt: string;
	teardown_build_id: string;
	teardown_time: string;
};

class DeprovAirplaneTasks {
	deprovInfo: DeprovInfo;
	fairytaleName: string;

	constructor(fairytaleName: string, deprovInfo: DeprovInfo) {
		this.fairytaleName = fairytaleName;
		this.deprovInfo = deprovInfo;
	}

	public async disableSentryIfReady() {
		if (!this.hasTimeElapsed(this.deprovInfo.dns_removal_time)) {
			console.log("Not ready for DNS removal. Doing nothing.");
			return;
		}

		await this.transitionToState(
			"disable_customer_sentry_alerts",
			{fairytale_name: this.fairytaleName, organization: this.deprovInfo.organization},
			"sentry_disabled",
			"Disabling sentry."
		);
	}

	public async putInHoldGroup() {
		await this.transitionToState(
			"change_deploy_group_to_hold",
			{fairytale_name: this.fairytaleName, organization: this.deprovInfo.organization},
			"hold_group",
			"Putting in hold group."
		);
	}

	public async deleteDns() {
		await this.transitionToState(
			"delete_dns_records",
			{fairytale_name: this.fairytaleName, organization: this.deprovInfo.organization,
				aws_account_id: this.deprovInfo.aws_account_id},
			"waiting_for_teardown_time",
			"Deleting DNS records."
		);
	}

	public async moveToTerminatedIfReady() {
		if (!this.hasTimeElapsed(this.deprovInfo.teardown_time)) {
			console.log("Not ready for teardown. Doing nothing.")
			return;
		}

		await this.transitionToState(
			"move_account_to_ou",
			{fairytale_name: this.fairytaleName, organization: this.deprovInfo.organization,
				aws_account_id: this.deprovInfo.aws_account_id, target_ou: "terminated"},
			"in_terminated_ou",
			"Moving account to terminated OU."
		);
	}

	public async teardownPanther() {
		this.deprovInfo.teardown_attempt = String(Number(this.deprovInfo.teardown_attempt) + 1);
		if (Number(this.deprovInfo.teardown_attempt) > NUM_TEARDOWN_ATTEMPTS) {
			// Don't bother trying to manually teardown or even notifying.
			// Just go on with the process and close the AWS account.
			return await this.moveToSuspended();
		}

		const teardown_result = await DeprovAirplaneTasks.runAirplaneTask(
			"panther_teardown",
			{organization: this.deprovInfo.organization, region: this.deprovInfo.region,
				aws_account_id: this.deprovInfo.aws_account_id},
			"Kicking off process to teardown Panther (not waiting for completion)."
		);

		this.deprovInfo.deprovision_state = "teardown_in_progress";
		this.deprovInfo.teardown_build_id = teardown_result.output["build_id"];
		await this.updateDeprovInfo();
	}

	public async checkTeardownStatus() {
		const teardown_result = await DeprovAirplaneTasks.runAirplaneTask(
			"retrieve_teardown_panther_status",
			{organization: this.deprovInfo.organization, build_id: this.deprovInfo.teardown_build_id},
			"Getting teardown build status."
		);

		switch (teardown_result.output["build_status"]) {
			case "IN_PROGRESS":
				// Do not call the update deprov info Airplane task - nothing needs to be updated
				return;
			case "SUCCEEDED":
				this.deprovInfo.teardown_build_id = "none";
				this.deprovInfo.deprovision_state = "teardown_successful";
				break;
			default:
				this.deprovInfo.teardown_build_id = "none";
				this.deprovInfo.deprovision_state = "teardown_failed";
				break;
		}

		await this.updateDeprovInfo();
	}

	public async moveToSuspended() {
		await this.transitionToState(
			"move_account_to_ou",
			{fairytale_name: this.fairytaleName, organization: this.deprovInfo.organization,
				aws_account_id: this.deprovInfo.aws_account_id, target_ou: "suspended"},
			"in_suspended_ou",
			"Moving account to suspended OU."
		);
	}

	public async tagForClosing() {
		await this.transitionToState(
			"tag_aws_account_for_removal",
			{organization: this.deprovInfo.organization, aws_account_id: this.deprovInfo.aws_account_id},
			"tagged_for_closing",
			"Tagging account for AWS account closing."
		);
	}

	public async closeAwsAccount() {
		await this.transitionToState(
			"close_aws_account",
			{organization: this.deprovInfo.organization, aws_account_id: this.deprovInfo.aws_account_id},
			"aws_closed",
			"Closing AWS account."
		);
	}

	public async removeDeploymentFiles() {
		await DeprovAirplaneTasks.runAirplaneTask(
			"remove_deployment_files",
			{organization: this.deprovInfo.organization, fairytale_name: this.fairytaleName},
			"Removing deployment files."
		);

		await this.transitionToState(
			"update_vault_config",
			{add_or_remove: "Remove", fairytale_name: this.fairytaleName, airplane_test_run: false},
			"deployment_files_removed",
			"Removing AWS vault entry."
		);
	}

	public async notifyDeleteSnowflake() {
		await DeprovAirplaneTasks.runAirplaneTask(
			"get_snowflake_account_locator",
			{fairytale_name: this.fairytaleName, send_slack_msg: true},
			"Sending Slack message to delete Snowflake."
		);

		await this.updateDeprovInfo(true)
	}

	public static async readDeprovInfo() {
		return await DeprovAirplaneTasks.runAirplaneTask(
			"read_deprov_info",
			{},
			"Retrieving deprov info for all customers."
		);
	}

	public static async runAirplaneTask(taskName: string, args: AirplaneArgs, msg?: string) {
		if (msg) {
			console.log(msg);
		}
		const result = await airplane.execute(taskName, args);
		return result;
	}

	private async transitionToState(taskName: string, args: AirplaneArgs, state: string, msg: string) {
		const result = await DeprovAirplaneTasks.runAirplaneTask(taskName, args, msg);
		this.deprovInfo.deprovision_state = state;
		await this.updateDeprovInfo();
		return result;
	}

	private async updateDeprovInfo(isFinished: boolean = false) {
		await DeprovAirplaneTasks.runAirplaneTask("update_deprov_info",
			{fairytale_name: this.fairytaleName, dns_removal_time: this.deprovInfo.dns_removal_time,
				teardown_time: this.deprovInfo.teardown_time, aws_account_id: this.deprovInfo.aws_account_id,
				organization: this.deprovInfo.organization, region: this.deprovInfo.region,
				teardown_attempt: this.deprovInfo.teardown_attempt,
				teardown_build_id: this.deprovInfo.teardown_build_id,
				deprovision_state: this.deprovInfo.deprovision_state,
				is_finished: isFinished}
		);
	}

	private hasTimeElapsed(checkTimeStr: string) {
		return new Date() > new Date(checkTimeStr);
	}
}

async function performActionsBasedOnState(fairytaleName: string, deprovTasks: DeprovAirplaneTasks) {
	console.log(`===== Starting to process account ${fairytaleName} =====`);
	let prevState = "none";
	while (deprovTasks.deprovInfo.deprovision_state != prevState) {
		prevState = deprovTasks.deprovInfo.deprovision_state;
		await processState(deprovTasks);
	}
	console.log(`===== Finished processing account ${fairytaleName} =====`);
}

async function processState(deprovTasks) {
	switch(deprovTasks.deprovInfo.deprovision_state) {
		case "waiting_for_dns_time": return await deprovTasks.disableSentryIfReady();
		case "sentry_disabled": return await deprovTasks.putInHoldGroup();
		case "hold_group": return await deprovTasks.deleteDns();
		case "waiting_for_teardown_time": return await deprovTasks.moveToTerminatedIfReady();
		// Terminated OU and teardown failed should both teardown Panther. Same function for both cases is intentional.
		case "in_terminated_ou":
		case "teardown_failed":
			return await deprovTasks.teardownPanther();
		case "teardown_in_progress": return await deprovTasks.checkTeardownStatus();
		case "teardown_successful": return await deprovTasks.moveToSuspended();
		case "in_suspended_ou": return await deprovTasks.tagForClosing();
		case "tagged_for_closing": return await deprovTasks.closeAwsAccount();
		case "aws_closed": return await deprovTasks.removeDeploymentFiles();
		case "deployment_files_removed": return await deprovTasks.notifyDeleteSnowflake();
		default: throw RangeError("Invalid state: " + deprovTasks.deprovInfo.deprovision_state);
	}
}

export default airplane.workflow(
	{
		slug: "deprovision_customer_scheduled_process",
		name: "Deprovision Customer (Scheduled Process)",
		nodeVersion: "18",
		schedules: {
			weekday_hourly: {cron: "0 12-23 * * 1-5", description: "Runs hourly during working hours"}
		},
	},
	async () => {
		const readDeprovInfoRun = await DeprovAirplaneTasks.readDeprovInfo()

		for (let fairytaleName in readDeprovInfoRun.output) {
			let deprovTasks = new DeprovAirplaneTasks(fairytaleName, readDeprovInfoRun.output[fairytaleName]);
			if ("deprovision_state" in deprovTasks.deprovInfo) {
				await performActionsBasedOnState(fairytaleName, deprovTasks)
			}
		}
	}
)
