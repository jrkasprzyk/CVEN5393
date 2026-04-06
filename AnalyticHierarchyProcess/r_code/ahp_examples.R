library(ahp)
library(data.tree) #may not be needed


setwd("[your path here] /example_problem_yaml_files/") #replace with the path on your computer

#example 1: lunch
lunchAhp <- Load("lunch.yaml")
Calculate(lunchAhp)
Visualize(lunchAhp)
Analyze(lunchAhp)
AnalyzeTable(lunchAhp)

#example 2: water
waterAhp <- Load("waterCost.yaml")
Calculate(waterAhp)
Visualize(waterAhp)
Analyze(waterAhp)
AnalyzeTable(waterAhp)