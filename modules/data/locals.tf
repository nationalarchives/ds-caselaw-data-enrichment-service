locals {
  db = {
    staging = {
      deletion_protection = true
    }
    production = {
      deletion_protection = true
    }
  }
}
