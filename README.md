# DPM2400Neo4j
To obtain a Neo4j database for the European Banking authority (EBA) data point model (DPM) 2.4.0.0 download all csv files from the DPM240 zip file and run the below statement.
Be sure to replace ..\Neo4j with the folder where your Neo4j files should be stored and replace ..\DPM240 with the folder where you downloaded the csv files.

neo4jImport --into "..\Neo4j\dpm2400.graphdb" --nodes "..\DPM240\Neo4jCell.csv" --nodes "..\DPM240\Neo4jDataPointVersion.csv" --nodes "..\DPM240\Neo4jCliques.csv" --relationships "..\DPM240\Neo4jCellDataPointVersion.csv" --relationships "..\DPM240\Neo4jDataPointVersionCell.csv" --relationships "..\DPM240\Neo4jCliqueNodes.csv" --relationships "..\DPM240\Neo4jNodesClique.csv" --relationships "..\DPM240\Neo4jCliqueHierarchy.csv" --relationships "..\DPM240\Neo4jHierarchyClique.csv" --delimiter ";" --array-delimiter "|"

To generate such csv files for other oversions of the DPM below listed actions need to be performed.
First: download the latest/relevant version of the EBA DPM from http://www.eba.europa.eu/regulation-and-policy/supervisory-reporting/implementing-technical-standard-on-supervisory-reporting-data-point-model-
Next: open the access database and export the following tables to text files (semicolon as delimiter, no text qualifier): DataPointVersion, mvCellLocation, TableVersion, Dimension, Member
Finally: download both python 2.7 scripts and run the script dpmAsGraph
Note that this query will take several hours to compleet on a laptop (about 6 hours on a intel i5-5300U CPU @2.30GHz with 16 GB of RAM).

For some basic info on the DPM see infoDPM.
For some basic info on Neo4j see infoNeo4j.
For info about the nodes defined in the csv files Neo4jCell, Neo4jCellDataPointVersion, Neo4jCliqueNodes and Neo4jCliques, please see infoNodes.
For examples of queries which can be used as a starting point to perform analysis on the Neo4j database, please see infoAnalysis.

