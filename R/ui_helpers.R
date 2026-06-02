# UI helper — health status badge HTML
status_badge <- function(status_list) {
  tags$div(
    style = paste0(
      "display:inline-block; padding:10px 24px; border-radius:8px; ",
      "font-size:1.4em; font-weight:bold; color:#fff; ",
      "background-color:", status_list$color, ";"
    ),
    status_list$status
  )
}
