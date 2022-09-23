import airplane from "airplane";

export default airplane.workflow(
  {
    "slug": "create_new_customer_workflow",
    "name": "Workflow Testing",
    "parameters": {
      account_name: { type: "shorttext", required: true },
      customer_domain: { type: "shorttext", required: false },
      region: { type: "shorttext", required: true, options: [ "ap-northeast-1", "ap-south-1", "ap-southeast-1", "ap-southeast-2", "eu-central-1", "eu-west-1", "eu-west-2", "us-east-1", "us-east-2", "us-west-2"] },
      backend: { type: "shorttext", required: true, options: ["BYOSF", "Managed"] },
      first_name: { type: "shorttext", required: true },
      last_name: { type: "shorttext", required: true },
      email_address: { type: "shorttext", required: true },
      deploy_group: { type: "shorttext", required: true, default: "J", options: ["A", "B", "C", "D", "E", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"] },
      fairytale_name: { type: "shorttext" },
      salesforce_account_id: { type: "shorttext", required: false, regex: "^[a-zA-Z\d]{18}$" },
      salesforce_opportunity_id: { type: "shorttext", required: false, regex: "^[a-zA-Z\d]{18}$" },
      sales_phase: { type: "shorttext", required: false, options: ["trial", "contract", "internal", "proof_of_concept"] }
    },

  },
  async (params) => {
    const generateNamesRun = await airplane.execute("generate_fairytale_and_domain_names", {
      fairytale_name: params.fairytale_name,
      account_name: params.account_name,
      deploy_group: params.deploy_group,
      customer_domain: params.customer_domain
    });

    const fairytaleName = generateNamesRun.output.fairytale_name
    const customerDomain = generateNamesRun.output.customer_domain
    console.log(generateNamesRun.output)
  }
);
