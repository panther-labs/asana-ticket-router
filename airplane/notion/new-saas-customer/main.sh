#!/bin/sh -eu
# Linked to https://app.airplane.dev/t/new_saas_customer_notion [do not edit this line]

echo " Name	${PARAM_NAME}"
echo " Fairytale Name	${PARAM_FAIRYTALE_NAME}"
echo " AWS ID	${PARAM_AWS_ID}"
echo " Version	${PARAM_VERSION}"
echo " Region	${PARAM_REGION}"
echo " Backend	\"${PARAM_BACKEND}\""
echo " Group	${PARAM_GROUP}"
echo " PoC	${PARAM_POC}"
echo " Support Role	${PARAM_SUPPORT_ROLE}"
echo " @ Email	${PARAM_AT_EMAIL}"

DATABASE_ID="cc445b0819164efca9d281e8ea2efab7"

# https://developers.notion.com/reference/page#property-value-object

curl -X POST 'https://api.notion.com/v1/pages' \
  -H 'Authorization: Bearer '"${NOTION_API_KEY}" \
  -H 'Notion-Version: 2021-08-16' \
  -H 'Content-Type: application/json' \
  -d '{
  "parent": {
    "database_id": "'"${DATABASE_ID}"'"
  },
  "properties": {
    "Fairytale Name": {
      "title": [
        {
          "text": {
            "content": "'"${PARAM_FAIRYTALE_NAME}"'"
          }
        }
      ]
    },
    "Name": {
      "rich_text": [
        {
          "text": {
            "content": "'"${PARAM_NAME}"'"
          }
        }
      ]
    },
    "AWS ID": {
      "rich_text": [
        {
          "text": {
            "content": "'"${PARAM_AWS_ID}"'"
          }
        }
      ]
    },
    "Version": {
      "select": {
        "name": "'"${PARAM_VERSION}"'"
      }
    },
    "Region": {
      "select": {
        "name": "'"${PARAM_REGION}"'"
      }
    },
    "Backend": {
      "select": {
        "name": "'"${PARAM_BACKEND}"'"
      }
    },
    "Group": {
      "select": {
        "name": "'"${PARAM_GROUP}"'"
      }
    },
    "PoC": {
      "checkbox": '${PARAM_POC}'
    },
    "Support Role": {
      "rich_text": [
        {
          "text": {
            "content": "'"${PARAM_SUPPORT_ROLE}"'"
          }
        }
      ]
    },
    "Email": {
      "email": "'"${PARAM_EMAIL}"'"
    }
  },
  "children": []
}'
