locals {
  vpc = {
    staging = {
      single_ngw = true
    }
    prod = {
      single_ngw = false
    }
  }
}
