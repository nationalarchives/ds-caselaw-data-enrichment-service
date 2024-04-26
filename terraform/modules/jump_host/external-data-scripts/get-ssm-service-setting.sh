#!/bin/bash

set -e
set -o pipefail

eval "$(jq -r '@sh "SSM_SERVICE_SETTING_ID=\(.setting_id)"')"

SERVICE_SETTING="$(aws ssm get-service-setting --setting-id "$SSM_SERVICE_SETTING_ID" | jq -cr '.ServiceSetting')"

jq -ncr --argjson service_setting "$SERVICE_SETTING" \
  '$service_setting | {
    setting_id: .SettingId,
    setting_value: .SettingValue,
    last_modified_date: .LastModifiedDate,
    last_modified_user: .LastModifiedUser,
    arn: .ARN,
    status: .Status
  }'
