args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
  stop("Usage: Rscript r_bnlearn_driver.R <input_csv> <method> <output_csv>")
}

input_path <- args[1]
method_name <- args[2]
output_path <- args[3]

suppressMessages(library(bnlearn))

df <- read.csv(input_path, stringsAsFactors = FALSE, check.names = FALSE)
for (column_name in names(df)) {
  df[[column_name]] <- as.factor(df[[column_name]])
}

if (method_name == "mmhc") {
  learned <- mmhc(df)
} else if (method_name == "h2pc") {
  learned <- h2pc(df)
} else if (method_name == "hpc") {
  learned <- hpc(df)
} else {
  stop(paste("Unsupported method:", method_name))
}

edge_df <- arcs(learned)
if (is.null(edge_df) || nrow(edge_df) == 0) {
  edge_df <- data.frame(from = character(), to = character())
}

write.csv(edge_df, output_path, row.names = FALSE)
