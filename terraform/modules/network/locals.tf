locals {
  vpc = {
    staging = {
      single_ngw = true
    }
    production = {
      single_ngw = false
    }
  }
}
