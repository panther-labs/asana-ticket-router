import airplane from "airplane";

export default airplane.workflow(
  {
    "slug": "hello_workflow",
    "name": "Hello Workflow",
    "parameters": {
      account_name: { type: "shorttext", required: false },
      // customDomain: { type: "shorttext", required: false },
      // region: { type: "shorttext", required: true, options: ["us-west-2"] },
      // backend: { type: "shorttext", required: true, options: ["BYOSF", "Managed"] },
      // firstName: { type: "shorttext", required: true },
      // lastName: { type: "shorttext", required: true },
      // emailAddress: { type: "shorttext", required: true },
      deploy_group: { type: "shorttext", required: true, options: ["A", "B", "C", "E", "J", "H", "I", "J", "K", "L", "M", "N", "O", "P"] },
      // fairytaleName: { type: "shorttext" },
      // salesforceAccountId: { type: "shorttext" },
      // salesforceOpportunityId: { type: "shorttext" },
      // salesPhase: { type: "shorttext" }
    }
  },
  async (params) => {
    const taskSlug = "generate_fairytale_and_domain_names";
    const generateNamesRun = await airplane.execute(taskSlug, {
      // fairytale_name: params.fairytaleName,
      account_name: params.account_name,
      deploy_group: params.deploy_group,
      // customer_domain: params.customDomain
    });
    console.log(generateNamesRun.output)
  }
);
