# Spark

1. extraction-framework/dump dir
   
`cd $extraction-framework/dump`

1. edit extraction.spark.properties
   
edit `$extraction-framework/dump/extraction.spark.properties`.

1. run spark extraction framework
   
`../run sparkextraction extraction.spark.properties`

# Maven

1. mvn clean install (install dependencies)

`mvn clean install`

2. mvn clean package (builds uberjar file)

`mvn clean package`