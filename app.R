library(shiny)

source("R/kinetics.R")
source("R/ui_helpers.R")

ui <- fluidPage(
  tags$head(tags$link(rel = "stylesheet", href = "styles.css")),

  titlePanel(
    div(
      tags$h2("AquaKinetics", class = "app-title"),
      tags$p("Aquaponic Biofilter Health Calculator", class = "app-subtitle")
    )
  ),

  sidebarLayout(
    sidebarPanel(
      numericInput("volume",      "Fish Tank Volume (litres)",   value = 600,  min = 10,  max = 50000, step = 10),
      numericInput("feed",        "Daily Feed Amount (grams)",   value = 80,   min = 1,   max = 10000, step = 5),
      numericInput("temperature", "Water Temperature (°C)",      value = 25,   min = 5,   max = 35,    step = 0.5),
      numericInput("ph",          "pH",                          value = 7.5,  min = 5,   max = 9,     step = 0.1),
      actionButton("run", "Calculate", class = "btn-primary btn-block",
                   style = "margin-top:12px;")
    ),

    mainPanel(
      fluidRow(
        column(12,
          h4("Biofilter Health Status"),
          uiOutput("status_badge"),
          p(id = "status_message", textOutput("status_msg"))
        )
      ),
      hr(),
      fluidRow(
        column(12,
          h4("72-Hour Ammonia Forecast (mg/L NH₃-N)"),
          plotOutput("ammonia_plot", height = "380px")
        )
      ),
      hr(),
      fluidRow(
        column(6,
          h5("Production Rate"),
          verbatimTextOutput("prod_rate_out")
        ),
        column(6,
          h5("Peak Ammonia (72 hr)"),
          verbatimTextOutput("peak_nh3_out")
        )
      )
    )
  )
)

server <- function(input, output, session) {

  curve_data <- eventReactive(input$run, {
    req(input$volume > 0, input$feed > 0,
        input$temperature >= 5, input$temperature <= 35,
        input$ph >= 5, input$ph <= 9)
    simulate_ammonia_curve(
      feed_g   = input$feed,
      volume_l = input$volume,
      temp_c   = input$temperature,
      ph       = input$ph
    )
  }, ignoreNULL = FALSE)  # run once on startup with defaults

  status <- reactive({
    df <- curve_data()
    health_status(tail(df$nh3_mg_l, 1))
  })

  output$status_badge <- renderUI({
    status_badge(status())
  })

  output$status_msg <- renderText({
    status()$message
  })

  output$ammonia_plot <- renderPlot({
    df  <- curve_data()
    st  <- status()

    par(mar = c(4, 5, 1, 1), bg = "#f4f7fb")
    plot(df$hour, df$nh3_mg_l,
         type = "l", lwd = 2.5, col = st$color,
         xlab = "Time (hours)",
         ylab = expression(NH[3]*"-N  (mg/L)"),
         ylim = c(0, max(df$nh3_mg_l, 3.5) * 1.1),
         las  = 1)

    # Threshold bands
    abline(h = 1.0, lty = 2, col = "#f39c12", lwd = 1.2)
    abline(h = 3.0, lty = 2, col = "#e74c3c", lwd = 1.2)
    legend("topright",
           legend = c(expression(NH[3]*"-N"), "Warning (1 mg/L)", "Critical (3 mg/L)"),
           col    = c(st$color, "#f39c12", "#e74c3c"),
           lty    = c(1, 2, 2), lwd = c(2.5, 1.2, 1.2),
           bty    = "n", cex = 0.85)

    grid(col = "#d9e3f0", lty = 1)
  })

  output$prod_rate_out <- renderText({
    rate <- ammonia_production_rate(input$feed, input$volume)
    sprintf("%.4f mg NH3-N / L / hr", rate)
  })

  output$peak_nh3_out <- renderText({
    df <- curve_data()
    sprintf("%.3f mg/L", max(df$nh3_mg_l))
  })
}

shinyApp(ui, server)
