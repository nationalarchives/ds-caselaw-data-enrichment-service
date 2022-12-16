# IAM group with admin policy attached. Users manually created and added to group.
resource "aws_iam_group" "admins" {
  name = "admins"
}

resource "aws_iam_group_policy_attachment" "admin" {
  group = aws_iam_group.admins.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_account_password_policy" "iam_password_policy" {
  minimum_password_length        = 14
  require_lowercase_characters   = true
  require_numbers                = true
  require_uppercase_characters   = true
  require_symbols                = true
  allow_users_to_change_password = true
}
