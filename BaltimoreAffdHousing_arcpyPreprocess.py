# Andrew Yen 2018
#
#
# Python script used to preprocess Baltimore urban development data using the arcpy site package
#
#
#

import sys, os
import arcpy
from arcpy import da, env


env.workspace = env.scratchGDB
work_path = env.workspace

env.overwriteOutput = True



#Feature Classes
census_fc = 'https://services1.arcgis.com/mVFRs7NF4iFitgbY/arcgis/rest/services/VS16_CensusDemographics/FeatureServer/0'
housing_fc = 'https://services1.arcgis.com/mVFRs7NF4iFitgbY/arcgis/rest/services/VS16_Housing/FeatureServer/0'

econview_fc = arcpy.GetParameterAsText(0)



econview_sel = arcpy.SelectLayerByAttribute_management(econview_fc, where_clause="Pro_type = 'Residential' AND Pro_Desc LIKE '%affordable%'")

affrdhous = arcpy.CopyFeatures_management(econview_sel, os.path.join(work_path, "affrdhous"))

affr_byCSA = arcpy.SpatialJoin_analysis(census_fc, 
                                        affrdhous, 
                                        out_feature_class=os.path.join(work_path, "affr_byCSA"), 
                                        match_option='CONTAINS')


#Compare median house sale price between CSAs White > 70% and Black > 70%

#Join housing and census tables to select 70% White or Black
hBlkWht = arcpy.SpatialJoin_analysis(affr_byCSA, 
                                     housing_fc, 
                                     out_feature_class=os.path.join(work_path, "hBlkWht"),
                                     match_option='INTERSECT'
                                    )


#Select CSAs (now with housing data) that are at least 70% Black and Extract
Blk_sel = arcpy.SelectLayerByAttribute_management(hBlkWht, where_clause="paa16 > 70")
CSA70blk = arcpy.CopyFeatures_management(Blk_sel, os.path.join(work_path, "CSA80blk"))


#Select CSAs (now with housing data) that are at least 70% White and Extract
Wht_sel = arcpy.SelectLayerByAttribute_management(hBlkWht, where_clause="pwhite16 > 70")
CSA70wht = arcpy.CopyFeatures_management(Wht_sel, os.path.join(work_path, "CSA80wht"))


#Find average median house sale price for CSAs 70% black and CSAs 70% white, the number of affordable housing projects,
#and the average vacancy rate. 
med_blk_price = arcpy.Statistics_analysis(CSA70blk, 
                                         os.path.join(work_path, "med_blk_price"), 
                                         statistics_fields=[["salepr16", 'MEAN'], ["Join_Count", 'SUM'], ["vacant16", 'MEAN']])
med_wht_price = arcpy.Statistics_analysis(CSA70wht, 
                                          os.path.join(work_path, "med_wht_price"), 
                                          statistics_fields=[["salepr16", 'MEAN'], ["Join_Count", 'SUM'], ["vacant16", 'MEAN']])



#Add new field indicating the majority race to both tables
field = 'maj_rac'
arcpy.AddField_management(med_blk_price, field, 'TEXT')

with da.UpdateCursor(med_blk_price, field) as cursor:
    for row in cursor:
        row[0] = "Black"
        cursor.updateRow(row)
    del cursor

arcpy.AddField_management(med_wht_price, field, 'TEXT')

with da.UpdateCursor(med_wht_price, field) as cursor:
    for row in cursor:
        row[0] = "White"
        cursor.updateRow(row)

#Merge tables for comparison
comp_CSAs = arcpy.Merge_management(['med_blk_price','med_wht_price'], os.path.join(work_path, "Compare_majCSAs"))


