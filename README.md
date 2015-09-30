# DPM2400Neo4j
To obtain a Neo4j database for the European Banking authority (EBA) datapoint model (DPM) 2.4.0.0 download all csv files from the DPM240 zip file and run the below statement.
Be sure to replace ..\Neo4j with the folder where your Neo4j files should be stored and replace ..\DPM240 with the folder where you downloaded the csv files.

neo4jImport --into "..\Neo4j\dpm2400.graphdb" --nodes "..\DPM240\Neo4jCell.csv" --nodes "..\DPM240\Neo4jDataPointVersion.csv" --nodes "..\DPM240\Neo4jCliques.csv" --relationships "..\DPM240\Neo4jCellDataPointVersion.csv" --relationships "..\DPM240\Neo4jDataPointVersionCell.csv" --relationships "..\DPM240\Neo4jCliqueNodes.csv" --relationships "..\DPM240\Neo4jNodesClique.csv" --relationships "..\DPM240\Neo4jCliqueHierarchy.csv" --relationships "..\DPM240\Neo4jHierarchyClique.csv" --delimiter ";" --array-delimiter "|"

To generate such csv files for other oversions of the DPM below listed actions need to be performed.
First: download the latest/relevant version of the EBA DPM from http://www.eba.europa.eu/regulation-and-policy/supervisory-reporting/implementing-technical-standard-on-supervisory-reporting-data-point-model-
Next: open the access database and export the following tables to text files (semicolon as delimiter, no text qualifier): DataPointVersion, mvCellLocation, TableVersion, Dimension, Member
Finally: download both python 2.7 scripts and run the script dpmAsGraph
Note that this query will take several hours to compleet on a laptop (about 6 hours on a intel i5-5300U CPU @2.30GHz with 16 GB of RAM).

Some basic info on the DPM:
Every cell of the single rule book reports (corep, finrep, etc) is linked to at most one datapointversion. A cell without a datapointversion is a greyed out cell (never gets any values).
One datapointversion is linked to one or more cells. Cells which are linked to the same datapointversion must contain the same value.
A datapointversion has a technical key (the datapointvid) and a functional key (the categorisation key) as such the terms datapointversion and categorisation key are interchangeble.
The categorisation key is a concatenation (in alphabetical order) of the dimension code and member id tuples which are relevant for it.
Each categorisation key has one metric dimension. The corresponding member describes what kind of value is to be reported in a cell. The other dimension member tuples describe the context of the cell (what kind of positions should be reported there).
For further details about the EBA DPM please see the eba website (http://www.eba.europa.eu/regulation-and-policy/supervisory-reporting/implementing-technical-standard-on-supervisory-reporting-data-point-model-).

Some basic info on Neo4j:
Neo4j is a graphical database. There is a free community edition.
A graphical database contains 2 basic elements: nodes and links. Nodes can have labels, links are of a certain type and both have properties.
It comes with a rather intuitive query language called cypher which allows the user to analyse the database.
To download and install Neo4j or for further info on Neo4j and on cypher (excellent tutorial available), please see http://neo4j.com/

Info on the csv files
The DPM cells and categorisation keys are nodes of the graph.
The links between cells and categorisation keys are links of the graph.
When categorisation keys have the same dimensions and all but 1 of these dimensions have identical members than these are considered similar.
Similar categorisation keys get linked to cliques (cliques are also nodes of the graph). The clique is identified by the common dimension member tuples.
If the clique identifier matches with an existing categorisation key, these get linked to each other (that categorisation key is considered as a parent of the clique).


For info about the nodes defined in the csv files Neo4jCell, Neo4jCellDataPointVersion, Neo4jCliqueNodes and Neo4jCliques, please see infoNodes.
For examples of queries which can be used as a starting point to perform analysis on the Neo4j database, please see infoAnalysis.

