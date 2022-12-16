locals {
  db = {
    staging = {
      deletion_protection = false
    }
    prod = {
      deletion_protection = true
    }
  }
}
