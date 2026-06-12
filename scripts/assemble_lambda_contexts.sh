#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="${REPO_ROOT}/src"

cd "${SRC_DIR}"

# UPDATE_LEGISLATION_TABLE
rm -rf lambdas/update_legislation_table/utils lambdas/update_legislation_table/database
mkdir -p lambdas/update_legislation_table/utils lambdas/update_legislation_table/database
cp -r utils/*.py lambdas/update_legislation_table/utils/
cp -r database/*.py lambdas/update_legislation_table/database/

# UPDATE_RULES_PROCESSOR
rm -rf lambdas/update_rules_processor/utils lambdas/update_rules_processor/database
mkdir -p lambdas/update_rules_processor/utils lambdas/update_rules_processor/database
cp -r utils/*.py lambdas/update_rules_processor/utils/
cp -r database/*.py lambdas/update_rules_processor/database/

echo "Assembled lambda build contexts under ${SRC_DIR}/lambdas"
