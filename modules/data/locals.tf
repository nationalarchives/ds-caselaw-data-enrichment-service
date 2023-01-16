locals {
  db = {
    staging = {
      deletion_protection = true
    }
    prod = {
      deletion_protection = true
    }
  }
}
