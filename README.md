# README #

Jupyter Notebook for creating GML spatial extents

### What is this repository for? ###

* Reading data files and generating GML spatial extents
* Because most datasets are very different, the process is roughly divided into 
    * read the coordinates of the data file into a geodataframe
    * aggregate the coordinates into the necessary shapely geometry type
    * simplify/dissolve/sample the geometries with the goal of reducing the number of coordinates to a reasonable number but
    * write the geometries to GML, insert into a XML document

### How do I get set up? ###

* each dataset is a branch
    * branch off main, name branch with dataset id and data type/format and geometry type
        * ex - R1.x137.000:0001-nc-drifter-multiline
    * branches are merged into main to incorporate improvements/features
    * branches are not deleted, so that
        * it's possible to go back to a previous dataset and rerun the extent
        * more importantly copy the dataset reader portion for a similar dataset

