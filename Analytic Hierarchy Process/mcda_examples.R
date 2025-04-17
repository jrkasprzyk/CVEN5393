library(ahp)
library(data.tree) #may not be needed
setwd("G:/My Drive/Finance/Real Estate") #replace with your drive

lunchAhp <- Load("lunch.yaml")

Calculate(lunchAhp)
Visualize(lunchAhp)
Analyze(lunchAhp)
AnalyzeTable(lunchAhp)

waterAhp <- Load("waterCost.yaml")
Calculate(waterAhp)
Visualize(waterAhp)
Analyze(waterAhp)
AnalyzeTable(waterAhp)