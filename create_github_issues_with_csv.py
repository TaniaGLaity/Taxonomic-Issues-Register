"""Create GitHub issues with CSV using GitHub CLI """

import argparse
import asyncio
import csv
import io
import sys
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE
from asyncio.tasks import as_completed
from pprint import pprint
from functools import partial
from typing import Generator

REPO = "[TaniaGLaity]/[Taxonomic-Issues-Register]"
PROJECT = "[Taxonomy]"
DATA = """
Summary,Assignees,Status,Issue key,Issue id,Description,Category,Priority,Reporter,Created,Issue URL,Comment,Higher Level Issue
Correction synonomies in Erochilus,,To Do,TAX-51,10131,ALA is not correctly representing APC taxonomy in Eriochilus. Eriochilus dilatatus subsp. brevifolius (Benth.) Hopper & A.P.Br. is the APC approved name for Eriochilus dilatatus subsp. undulatus. Eriochilus glareosus G.Brockman & C.J.French is the APC current name for Eriochilus sp. Roleystone (G. Brockman 1140). ALA currently refers Eriochilus sp. Roleystone (G. Brockman 1140) incorrectly to Eriochilus dilatatus subsp. undulatus. ALA does not have Eriochilus glareosus G.Brockman & C.J.French as a valid taxa and also shows both Eriochilus dilatatus subsp. undulatus and Eriochilus dilatatus subsp. brevifolius (Benth.) Hopper & A.P.Br as accepted taxa.,Incorrect Synonomy,Urgent,Cam Slatyer,Cam Slatyer,,Issue raised by Cam October 2022,APC names load not correctly interpreting APC preferred name
Correction synonomies in Goodenia,,To Do,TAX-50,10130,"ALA is not correctly referencing synonymies in Goodenia. Goodenia pritzelii is on the WA sensitive species list. Goodenia pritzelii Domin is a valid taxa according to APC (2006). The ALA matches this taxon incorrectly to Goodenia microptera F.Muell., also a valid taxon according to APC 2007",Incorrect Synonomy,Urgent,Cam Slatyer,Cam Slatyer,,Issue raised by Cam October 2022,APC names load not correctly interpreting APC preferred name
Rhinonicteris aurantia (Pilbara) data not attaching correctly,,To Do,TAX-49,10129,The listed species Rhinonicteris aurantia (Pilbara) has an unranked taxa created for it however data is still attaching to the nominate species (Rhinonicteris aurantia),Name Matching,Urgent,Cam Slatyer,Cam Slatyer,,Issue raised by Cam October 2022,Data matching not attaching data to correct taxon
Listing not attaching to Acacia lasiocarpa var. lasiocarpa Cockleshell Gully variant (E.A. Griffin 2039) ,,To Do,TAX-48,10128,A taxon exists in ALA for listed species Acacia lasiocarpa var. lasiocarpa Cockleshell Gully variant (E.A. Griffin 2039) and has data attaching to it but listing and sensitivity  information is not attaching ,Threatened species,Urgent,Cam Slatyer,Cam Slatyer,,Issue raised by Cam October 2022,Data matching not attaching listing information to correct taxon
Lindernia eremophiloides incorrectly showing as a synonym of Vandellia eremophiloides,,To Do,TAX-47,10127,"ALA incorrectly shows listed species L. eremophiloides as a synonym of Vandellia eremophiloides. Instead, Vandellia eremophiloides (W.R.Barker) Eb.Fisch., Schäferh. & Kai Müll. Is a synonym of Lindernia eremophiloides W.R.Barker (APC 2020)",Incorrect Synonomy,Urgent,Cam Slatyer,Cam Slatyer,,Issue raised by Cam October 2022,APC names load not correctly interpreting APC preferred name
Lindernia macrosiphonia incorrectly showing as a synonym of Vandella eremophiloides,,To Do,TAX-46,10126,"ALA incorrectly shows the listed species Lindernia macrosiphonia (F.Muell.) W.R.Barker as a synonym of Vandellia macrosiphonia (F.Muell.) Eb.Fisch., Schäferh. & Kai Müll. According to APC 2021, Lindernia macrosiphonia (F.Muell.) W.R.Barker is the accepted species.",Incorrect Synonomy,Urgent,Cam Slatyer,Cam Slatyer,,Issue raised by Cam October 2022,APC names load not correctly interpreting APC preferred name
Lomandra acicularis incorrectly referred by ALA to Lomandra sp. Kimberley (M.D.Barrett 1036) WA Herbarium,,To Do,TAX-45,10125,ALA incorrectly refers listed species Lomandra acicularis ms M.D.Barrett to Lomandra sp. Kimberley (M.D.Barrett 1036) WA Herbarium and also has a separate entry for Lomandra acicularis M.D.Barrett. Lomandra acicularis M.D.Barrett is the correct current accepted name (APC 2021) and both Lomandra acicularis ms M.D.Barrett and Lomandra sp. Kimberley (M.D.Barrett 1036) WA Herbarium are junior synonyms,Incorrect Synonomy,Urgent,Cam Slatyer,Cam Slatyer,https://bie.ala.org.au/species/https://id.biodiversity.org.au/node/apni/2889512            https://bie.ala.org.au/species/Lomandra_acicularis,Issue raised by Cam October 2022,APC names load not correctly interpreting APC preferred name
,,,,,,,,,,,
Different NSL Namespaces for different taxon IDs in ALA,,To Do,TAX-44,10124,"The identifiers that the ALA uses as species ids use multiple NSL URIs. The odd thing is that they come from different namespaces. Fauna seem to come from the one AFD URI, however there are different classes of URI for the plant/moss/lichen taxa.  i.e. For the plants (APNI), the species ids are variously show as , ,  or . Mosses (AusMoss) are variously shown as ,  or  and lichens as  or . It looks very much like the ALA has ended up with a surprising mixture of records from different parts of the APNI/APC graph.  these URIs are as follows:

[https://biodiversity.org.au/afd/taxa/|https://biodiversity.org.au/afd/taxa/]
[https://id.biodiversity.org.au/https://id.biodiversity.org.au/name/apni/|https://id.biodiversity.org.au/https:/id.biodiversity.org.au/name/apni/] [https://id.biodiversity.org.au/instance/apni/|https://id.biodiversity.org.au/instance/apni/]
[https://id.biodiversity.org.au/instance/ausmoss/|https://id.biodiversity.org.au/instance/ausmoss/]
[https://id.biodiversity.org.au/name/apni/|https://id.biodiversity.org.au/name/apni/]
[https://id.biodiversity.org.au/node/apni/|https://id.biodiversity.org.au/node/apni/]
[https://id.biodiversity.org.au/node/ausmoss/|https://id.biodiversity.org.au/node/ausmoss/]
[https://id.biodiversity.org.au/node/lichen/|https://id.biodiversity.org.au/node/lichen/]
[https://id.biodiversity.org.au/taxon/apni/|https://id.biodiversity.org.au/taxon/apni/]
[https://id.biodiversity.org.au/taxon/ausmoss/|https://id.biodiversity.org.au/taxon/ausmoss/]
[https://id.biodiversity.org.au/taxon/lichen/|https://id.biodiversity.org.au/taxon/lichen/]",Name Matching,Low,Tania Laity,11/01/2023 15:22,,"issue raised by Donald 9/11/2022 - and commented that it could be that each node in APNI has multiple identifiers and this is simply lack of tidiness, but I think it would be worthwhile to explore how this variation comes to be."
Multiple entries of Thalassarche chlororhynchos on taxon tree,,To Do,TAX-43,10123,Multiple entries of Thalassarche chlororhynchos on taxon tree - two from NZOR and one from the Bonn Convention list.  Two out of three of these have records attached (not the same records),Duplicate Taxa,Low,Tania Laity,11/01/2023 15:12,,"issue raised by Donald 8/11/2022 who made the following recommendations: 

*Recommendation: If the ALA is going to use CAAB, a human reviewer should check the placement of taxa and correct issue before its contents are treated as Accepted taxa.*

*Recommendation: Do not use NZOR as a source for Accepted Australian taxa.*"
Taxon names matching to wrong Kingdom,,To Do,TAX-42,10122,"the placement of the other Accepted and Inferred Accepted names has used the ALA fuzzy matching and makes serious errors. Two more dreadful examples, both of molluscs (reported with animal classifications in CAAB) that have been grafted into Plantae e.g Mitrella dictua and Ficus. This means that, even when the ALA reports no fuzzy matching issues, fuzzy matching has occurred and degraded data.",Incorrect Taxonomy,Medium,Tania Laity,11/01/2023 15:07,,issue raised by Donald 8/11/22
inferred taxa from non-authoritative lists not marked with data quality flag,,To Do,TAX-41,10121,"The ALA uses the ANSL as the core of its taxonomic backbone (all of these taxa have HTTPS URIs as their ids), but supplements it with CAAB (numeric taxon ids) and NZOR ( taxon ids). These are all treated as . Additionally, there are other taxa that the ALA has included because they appear in other necessary sources (e.g.  or ) - these have taxon ids of the form  and are marked as  at the taxon level.  Occurrence records associated with any of these taxa have no taxonomic issue flags. In other words, they are shown as clean and beyond suspicion. I think the only way to find out that some are  would be to query the taxon records.  this causes issues for users when querying the data where they need to exclude records for these taxa (can't do it it using quality flag).",Invalid Names,Low,Tania Laity,11/01/2023 15:00,,"issue raised by Donald 8/11/22 who recommended the following:

*Recommendation: Users should be able to understand the taxonomic confidence for the taxon referenced in any occurrence record without having to download the taxonomy.* This could be a three-tier ranking: 1) ANSL, 2) Other trusted sources (CAAB, in particular) stitched in by ALA algorithms, 3) Anything else. Official users like ABARES want to know that they are using the trusted national taxonomy and that is ANSL."
Blechnum rupestre (Kaulf. ex Link) Christenh. x Blechnum medium (R.Br.) Christenh. returns error in ALA,,To Do,TAX-40,10120,h3. [_Blechnum_|https://bie.ala.org.au/species/Blechnum_rupestre_x_Blechnum_medium][ |https://bie.ala.org.au/species/Blechnum_rupestre_x_Blechnum_medium][_rupestre_|https://bie.ala.org.au/species/Blechnum_rupestre_x_Blechnum_medium][ (Kaulf. ex Link) Christenh. x |https://bie.ala.org.au/species/Blechnum_rupestre_x_Blechnum_medium][_Blechnum_|https://bie.ala.org.au/species/Blechnum_rupestre_x_Blechnum_medium][ |https://bie.ala.org.au/species/Blechnum_rupestre_x_Blechnum_medium][_medium_|https://bie.ala.org.au/species/Blechnum_rupestre_x_Blechnum_medium][ (R.Br.) Christenh.|https://bie.ala.org.au/species/Blechnum_rupestre_x_Blechnum_medium] appears on the taxonomic backbone in ALA but when the link to the species page / records for this species is clicked it returns an error. It is a legitimate taxon according to APNI,Invalid Names,Low,Tania Laity,11/01/2023 10:59,,Issue identified by Donald 8/11/2022
"Taxonomic Backbone vs Data Match vs Name Matching - name matching not recognising italicised vs no italics, same words in different combinations e.g. authors etc",,To Do,TAX-39,10080,"Why are there two combinations each of P.p. phylicifolia and P. p. ericoides? This is our own doing. In the case of Pomaderris phylicifolia subsp. ericoides, in one instance, the subsp. Is italicised, ridiculously causing the name to fail to match when we've loaded threatened species lists so the name has been manually added a second time. Fortunately no data has followed it, purely, I think, because the data-matching ignores (I suspect) italics¦. But our name matching clear +does+ take it into account¦

In the case of Pomaderris phylicifolia subsp. phylicifolia, again this is a problem of our own doing. The names matching has failed to recognise the same author names in different author combinations (subsp. phylicifoliaLodd. ex Lin versus Lodd.exLinksubsp.phylicifolia) when loading conservation lists and as a consequence we've added a different combination, being PomaderrisphylicifoliaLodd.exLinksubsp.phylicifolia. What makes this particularly annoying is that our taxonomy is correct. All the data has correctly been attributed with Pomaderris phylicifolia subsp. phylicifolia, however 32 records have the authorship descriptor Lodd. Ex Link instead of blank or (Maiden & Betche) N.G.Walsh & Coates. These data have been matched to the dodgy taxonomy entry.",Name Matching,Low,Tania Laity,10/01/2023 12:00,,"identified by Cam 21/12/22 - *Recommended solutions “ refer to the taxonomic working group, but actually develop a governance process for adding names from lists and review all unranked or presumed authority names already in the ALA*"
Taxonomic Name Search returns different results in BIE and Front End (),,To Do,TAX-38,10079,"type 1 errors technically aren't errors “ it's actually a limitation of using BIE that users should be clear about. IE “ BIE will always return the exact answer to the query name it is given. Therefore it will always return a subset of the total number of records if there are more than one possible taxonomic combination and therefore it is an unreliable means of querying the data for number of records at any taxonomic level. The only reliable means of querying the data and getting a correct answer is to use the front page, navigate to the species page and then use the classification page to check for actual or ALA-caused synonyms that may have additional data attached in the taxonomic tree.",Synonomy,Low,Tania Laity,10/01/2023 11:52,,identified by Cam 21/12/2022 - *Recommended solutions “ either a) change the BIE page so that it returns number of records the same way that the front end does (and also includes all possible taxonomic combinations) or (more simply) “ add text to the BIE alerting users to the limitations of the search function*
"Thinornis rubricollis to be made synonym of Thinornis cucullatus (Vieillot, 1818)",,To Do,TAX-37,10078,"Thinornis rubricollis to be made synonym of Thinornis cucullatus (Vieillot, 1818). Currently Thinornis rubricollis is an unranked taxon under genus in ALA.  On SA sensitive species list",Incorrect Taxonomy,Urgent,Tania Laity,10/01/2023 10:46,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/61ad6012-e658-483b-9cbc-0ead0934fd86#classification,issue raised by Cam 11/10/2022
"Pterostylis cucullata ssp. sylvicola, P. cucullata ssp. cucullata  synonyms of P. cucullata",,To Do,TAX-36,10077,"Pterostylis cucullata ssp. sylvicola, Pterostylis cucullata ssp. cucullata - to be made synonyms of Pterostylis cucullata in the ALA - according to APNI - species listed on SA sensitive species list",Incorrect Taxonomy,Urgent,Tania Laity,10/01/2023 10:46,https://bie.ala.org.au/species/https://id.biodiversity.org.au/taxon/apni/51412090#classification,issue raised by Cam 11/10/2022
"Prasophyllum parvicallum, Genoplesium parvicallum need to be synonyms of Corunastylis parvicalla",,To Do,TAX-35,10076,"Prasophyllum parvicallum, Genoplesium parvicallum need to be synonyms of Corunastylis parvicalla according to APNI.  ALA currently shows the wrong accepted name as G. parvicallum. Need to update taxonomic backbone.  Listed on Qld sensitive species list",Incorrect Taxonomy,Urgent,Tania Laity,10/01/2023 10:46,https://bie.ala.org.au/species/https://id.biodiversity.org.au/taxon/apni/51406041#classification,issue raised by Cam 11/10/2022
PHA list unmatched names - due to records being matched at higher taxon levels,,To Do,TAX-34,10075,"there appear to be a significant number of viruses, fungi and microbes that say on the PHA list that they match to a record, but when you click on the record you get either an error saying the record doesn-t exist or it simply doesn-t go anywhere. however records exist in the ALA but have been name matched to higher level taxa e.g. family or order",Name Matching,Medium,Tania Laity,10/01/2023 10:46,,issue identified by cam 24/06/2022
Petrogale lateralis subsp. (WAM M15135) -  needs to be created as an unranked taxon,,To Do,TAX-33,10074,Petrogale lateralis subsp. (WAM M15135) -  needs to be created as an unranked taxon under Petrogale lateralis as it is listed on WA sensitive species list - currently records assigned to genus,Name Matching,Urgent,Tania Laity,10/01/2023 10:46,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/e82506d7-3e9e-4086-98f3-a08ca07d2a97,issue raised by Cam 11/10/2022
Petrogale lateralis subsp. (ANWC CM15314) - needs to be created as an unranked taxon,,To Do,TAX-32,10073,Petrogale lateralis subsp. (ANWC CM15314) -  needs to be created as an unranked taxon under Petrogale lateralis as it is listed on WA sensitive species list - currently records assigned to genus,Name Matching,Urgent,Tania Laity,10/01/2023 10:46,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/e82506d7-3e9e-4086-98f3-a08ca07d2a97,issue raised by Cam 11/10/2022
Petaurus australis - subspecies,,To Do,TAX-31,10072,"Petaurus australis is split into two subspecies - which are listed as threatened in Qld, NSW, SA and EPBC.  the two subspecies are split geographically and all records are shown at the species level and the taxonomy appears to be correct.  However...  the species pages and conservation status is not correctly attributed.  The northern subspecies is listed in both Qld and on EPBC but currently is only showing as threatened on EPBC with no records attributed to it.  The south-eastern subspecies is only showing records for Qld but should be showing ALL records in NSW and Vic and is only showing conservation status in Qld and EPBC - it should be showing as threatened in NSW and SA (these latter two statuses are showing at the species level only)",Taxon Splits,High,Tania Laity,10/01/2023 10:46,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/b3a61169-1e3c-4d6e-904f-f4d643df13a6,raised by Cam initially with additional issues wrt the lists on 28/4/2022 and 05/05/2022 (the issues in this tickets were not resolved)
Perameles gunnii - subspecies need to be removed,,To Do,TAX-30,10071,There are no subspecies for Perameles gunnii. Therefore all the subspecies shown in the list should be removed. The population in Tasmania is listed on EPBC but there is no taxonomic difference between offshore and mainland populations. All the variants below species level are synonyms (real or imagined) of the species and should be attributed to the species,Invalid Names,High,Tania Laity,10/01/2023 10:46,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/03b41280-eed3-4244-bf2e-bc8f7c30b3df#classification,issue raised by Cam 03/05/2022
Perameles bougainville infrasp. fasciata should be a synonym of Perameles fasciata,,To Do,TAX-29,10070,Perameles bougainville infrasp. fasciata should be a synonym of Perameles fasciata - currently listed separately on the taxonomic backbone - need to synonymise,Synonomy,High,Tania Laity,10/01/2023 10:46,https://bie.ala.org.au/species/ALA_DR650_907#classification,issue raised by Cam 03/05/2022
non-geographic species splits and points allocations,,To Do,TAX-28,10069,non-geographic species splits and points are not allocated correctly - often the original species plus the new ones are added to the taxonomic backbone - can impact on sensitive species where obfuscation rules are not applied correctly,Taxon Splits,High,Tania Laity,10/01/2023 10:46,,
Lists not matching to the correct taxonomic level,,To Do,TAX-27,10068,scientific names in lists not matching to the correct level on the ALA taxonomic backbone - often allocated to a higher taxon e.g. a subspecies on a list matching to a species - this is particularly an issue where these lists are of sensitive species or threatened species,Name Matching,High,Tania Laity,10/01/2023 10:46,,
Leucoptera (moth) species page is linking to information for plant genus,,To Do,TAX-26,10067,Leucoptera (moth) species page is linking to information for plant genus Leucoptera from wikipedia,Name Matching,Medium,Tania Laity,10/01/2023 10:46,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/01b7a1bb-2687-4fc5-8479-eafe2d8e078f,issue flagged by user via helpdesk August 2022 - issue unresolved
Isodorella newcombi synonym of Isidorella newcombi,,To Do,TAX-25,10066,"Currently observations with the raw scientific name Isodorella newcombi are being matched to the family, Planorbidae and they should be matched as a synonym of Isidorella newcombi.  Need to add synonym and ensure the observations are attached to the species",Name Matching,Medium,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/7bbde653-7c32-453a-95d8-0e46d105210b#classification,issue raised by Cam 27/06/2022
Hylacola pyrrhopygia parkeri duplicated,,To Do,TAX-24,10065,"Hylacola pyrrhopygia parkeri should be made a synonym of Hylacola pyrrhopygia parkeri (Schodde & Mason, 1999) - duplicated on taxonomic backbone - the former has no records / information attributed to it.",Duplicate Taxa,Medium,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/ALA_DR656_999#overview,issue identified by Cam 03/05/2022 - partially resolved only
"Hylacola cauta halmanturina duplicate of Hylacola cauta halmaturinus (Mathews, 1912)",,To Do,TAX-23,10064,"Hylacola cauta halmaturina should be listed as a synonym of Hylacola cauta halmaturinus (Mathews, 1912) - currently there are duplicate taxa on the backbone",Duplicate Taxa,Medium,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/ALA_DR656_998#overview,issue identified by Cam 03/05/2022 - partially resolved only
Hurleya sp. (WAM642-97)- needs to be created as an unranked taxon,,To Do,TAX-22,10063,Hurleya sp. (WAM642-97) - needs to be created as an unranked taxon under Hurleya as it is listed on WA sensitive species list - currently records assigned to genus,Name Matching,Urgent,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/e278f70e-5d79-49e8-b61f-7f932de3bd6c,Issue raised by Cam 11/10/2022
Hemiergis sp. 'koontoolasi' - needs to be created as an unranked taxon,,To Do,TAX-21,10062,Hemiergis sp. 'koontoolasi' - needs to be created as an unranked taxon under Hemiergis as it is listed on WA sensitive species list - currently records assigned to genus,Name Matching,Urgent,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/f40f2d88-96ec-4595-ba95-4ee9a49a48fa,issue identified by Cam 11/10/2022
Haitia acuta to be synonymised to Physa acuta,,To Do,TAX-20,10061,Observations with the name Haitia acuta are currently attached to the familiy Physidae - they need to be synonymised to Physa acuta and observations updated to reflect this,Name Matching,Medium,Tania Laity,10/01/2023 10:45,https://biocache.ala.org.au/occurrences/364617e4-94bf-4178-b0bb-a986ee96d7d1,issue raised by Cam 27/06/2022
geographic species splits not being handled correctly,,To Do,TAX-19,10060,"E.g. widespread species split into 3 new species geographically, all critically endangered. - ALA adds the new taxonomy but doesn't update the allocation of points to new taxonomy - so the ALA ends up with four species - the original species (with all the museum data, now accurately revealing the location of critically endangered species) and three new species, all obfuscated correctly)",Taxon Splits,High,Tania Laity,10/01/2023 10:45,,
Falco novaseseelandiae duplicated,,To Do,TAX-18,10059,Two entries of Falco novaeseelandiae occur on the taxonomic backbone - they should be synonymised,Duplicate Taxa,Low,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/NZOR-6-81413#overview,issue raised by Cam 10/05/2022
Eria intermedia and Eria dischorensis should be synonyms of Bryobium dischorense,,To Do,TAX-17,10058,Eria intermedia and Eria dischorensis should be synonyms of Bryobium dischorense according to APNI - listed on QLD sensitive species list. need to add Bryobium dischorense as accepted name on taxonomic backbone and change Eria intermedia and Eria dischorensis to synonyms of this.,Incorrect Taxonomy,Urgent,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/https://id.biodiversity.org.au/taxon/apni/51405048#,issue identified by Cam 11/10/2022
Duplicate species pages Eucalyptus Cattai,,To Do,TAX-16,10057,Eucalyptus sp. Cattai (listed in NSW) and Eucalyptus sp. Cattai (Gregson s.n. 28 Aug 1954) NSW Herbarium (listed under EPBC and the APC Accepted Name) are both linked to Eucalyptus Cattai on the taxonomic backbone but don't appear in the tree under Eucalyptus.  they need to be synonymised,Duplicate Taxa,High,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/ALA_DR650_899#classification,issue identified by user 31/08/2022
Cycas media subsp. media - C.ophiolitica - new unranked taxon required,,To Do,TAX-15,10056,Cycas media subsp. media - C.ophiolitica - needs to be created as an unranked taxon under Cycas as it is listed on Qld sensitive species list - currently records assigned to genus,Name Matching,Urgent,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/https://id.biodiversity.org.au/node/apni/2887109#names,issue identified by Cam 11/10/2022
Corybas X dentatus duplicate of C. dentatus,,To Do,TAX-14,10055,Corybas X dentatus - https://bie.ala.org.au/species/ALA_DR653_1082#overview - (listed in SA as endangered) is listed separately (as an unranked taxon) to Corybas dentatus - https://bie.ala.org.au/species/https://id.biodiversity.org.au/taxon/apni/51401031#overview -  (listed as vulnerable on EPBC). These are the same taxon and should be synonymised,Duplicate Taxa,High,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/ALA_DR653_1082#overview,slightly different but related issue to that raised by Cam to Peggy on 1/4/2022. High priority as these taxa are threatened species
Canis lupus familaris should be a synonym of Canis familiaris,,To Do,TAX-13,10054,Canis lupus familaris should be a synonym of Canis familiaris according to AFD.  there are two entries on the taxonomic backbone - they should be synonymised,Duplicate Taxa,Medium,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/NZOR-6-85973#classification,issue raised by Cam 9/05/22
Candalides geminus to be removed from sensitive species list for NT,,To Do,TAX-12,10053,Candalides geminus to be removed from sensitive species list for NT - requested by Damien Milne 23/03/2022,Sensitive Species,High,Tania Laity,10/01/2023 10:45,https://lists.ala.org.au/speciesListItem/list/dr492?q=Candalides+geminus+,requested by Damien Milne 23/03/2022. Cam followed up with Data Team 20/10/2022
Calyptorhynchus lathami lathami duplicates,,To Do,TAX-11,10052,Duplicate entries occur for Calyptorhynchus lathami lathami on the taxonomic backbone which need to be synonymised,Duplicate Taxa,Low,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/ALA_DR652_147#overview,
Calyptorhynchus lathami halmaturinus duplicated,,To Do,TAX-10,10051,Duplicate entries of Calyptorhynchus lathami halmaturinus occur on taxonomic backbone and need to be synonymised,Duplicate Taxa,Low,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/ALA_DR656_388#classification,
Caladenia vulgaris var. nunguensis request to add to Tas Sensitive Species list,,To Do,TAX-9,10050,Caladenia vulgaris var. nunguensis has been requested to be added to the Tas sensitive species list in ALA - but not recognised var by APNI / APC.  Recognised by Kew Gardens and is an Tas endemic. doesn't appear to have any records with the sub-specific name in ALA.  Need to clarify if accepted name and add to taxonomic backbone and Tas Sensitive Species list if it is.,New Taxon,Urgent,Tania Laity,10/01/2023 10:45,https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:77219698-1,request by Tas to add to sensitive species list - 21/09/2022 and reminder sent to data team 20/10/2022. Issue not resolved
Caladenia dilatata matching to Genus,,To Do,TAX-8,10049,Caladenia dilatata matching to Genus on the Qld and SA sensitive species lists - resulting in unobfuscated records being released publicly.  need to match to species on both this lists an apply obfuscation rules,Name Matching,Urgent,Tania Laity,10/01/2023 10:45,https://lists.ala.org.au/speciesListItem/list/dr493?q=Caladenia+di,Issue identified by Cam 11/10/2022
Bryobium irukandjianum is listed as a synonym of Eria irukandjiana,,To Do,TAX-7,10048,Bryobium irukandjianum is listed as a synonym of Eria irukandjiana - should be the other way around i.e. Bryobium irukandjianum is the accepted name and Eria irukandjiana is a synonym according to APNI. Listed on QLD sensitive species list,Incorrect Synonomy,Urgent,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/https://id.biodiversity.org.au/taxon/apni/51405054,Issue identified by Cam 11/10/2022
Bettongia lesueur subspecies duplicated,,To Do,TAX-6,10047,Bettongia lesueur Barrow and Boodie Island subpecies have 3 separate entries on the taxonomic backbone. This subspecies is listed in both WA and on EPBC Act but the status is showing on separate entries,Duplicate Taxa,High,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/dedab6d7-623b-48e9-a36b-dff255b72af8#classification,Cam notified Peggy of this issue via email 10/05/2022
"Bellamya heudei guangdungensis synonym of Sinotaia heudei guangdungensis (Kobelt, 1906)",,To Do,TAX-5,10046,"Bellamya heudei guangdungensis is currently attached the the genus Sinotaia but is a synonym of Sinotaia heudei guangdungensis (Kobelt, 1906).  Need to add as a synonym and reattach records to subgenus not genus.  Similarly Sinotaia guangdungensi is a synonym of this subspecies and need to be attributed to it and observation records attached to the subspecies",Name Matching,Medium,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/8c2b695e-fced-4e9e-91f1-b577ac3584df#classification,issue raised by Cam 27/06/2022
Anilios torresianus attributed to genus - should be attributed to Anilios polygrammicus,,To Do,TAX-4,10045,Anilios torresianus attributed to genus - should be attributed to Anilios polygrammicus - QLD DES lists Anilios torresianus (north-eastern blind snake) with a synonym of Ramphotyphlops polygrammicus and Typhlops polygrammicus - AFD lists Typhlops polygrammicus as a synonym of Anilios polygrammicus,Name Matching,Medium,Tania Laity,10/01/2023 10:45,https://biocache.ala.org.au/occurrences/cb3cfe80-793a-4318-b1c3-01c6e51caee5,Issue URL relates to one example only - there are several records with the supplied name of Anilios torresianus which need to be resolved
Anilios sp. 'Cape Range' unranked - should be matched to Ramphotyphlops sp. Cape Range/A. splendidus,,To Do,TAX-3,10044,Ramphotyphlops sp 'Cape Range' - listed species in WA - unranked (no records)- not attached to taxonomic backbone - should be as listed in WA - and potentially could be matched to Anilios splendidus in ALA Adec Preview Generated PDF File (museum.wa.gov.au) as a synonym would need confirmation from WAM. Anilios sp. 'Cape Range' is listed in WA- unranked (no records) - not showing conservation status- not attached to taxonomic backbone - should be matched at least to genus and Ramphotyphlops sp 'Cape Range' or potentially to Anilios splendidus in ALA Adec Preview Generated PDF File (museum.wa.gov.au) as a synonym - would need confirmation with WAM,Name Matching,High,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/ALA_DR2201_3596#overview,identified as an issue by Cam 13/05/2022
"Amytornis (Magnamytis) striatus whitei Mathews, 1910 incorrect in ALA",,To Do,TAX-2,10043,"according to AFD Amytornis (Magnamytis) striatus whitei Mathews, 1910 in ALA is incorrect (it doesn't exist) - should be Amytornis (Magnamytis) whitei Mathews, 1910 - correct and elevate to species level in backbone.  Listed on SA sensitive species list",Incorrect Taxonomy,Urgent,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/da3196e7-c801-4201-b3e9-4e23cc811657#classification,issue identified by Cam 11/10/2022
Acanthaster solaris attributed to genus - synonym of Acanthaster planci,,To Do,TAX-1,10042,Acanthaster solaris attributed to genus - synonym of Acanthaster planci,Name Matching,High,Tania Laity,10/01/2023 10:45,https://bie.ala.org.au/species/https://biodiversity.org.au/afd/taxa/cdbfad4a-50c8-40e7-b323-f12573eb8d5d#overview,"Issue identified by Cam 13/05/2022 - email to Andre, Hamish, Ely, Erin and Lu"

"""

# Type aliases
Program = str
CommandArgs = list[str]
Command = tuple[Program, CommandArgs]
CommandOutput = tuple[str, str]


async def main() -> None:
    """Main function"""
    args = get_args()
    dry_run = args.dry_run

    issues = [x for x in read_data(DATA)]

    build_command_ = partial(build_command, body="", repo=REPO, project=PROJECT)
    commands = [
        build_command_(title=title, milestone=milestone) for milestone, title in issues
    ]

    if dry_run:
        pprint(commands)
        return

    await run_all(commands)


def get_args() -> argparse.Namespace:
    """Get CLI args"""
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--dry-run', action='store_true')
    return parser.parse_args()


def read_data(csv_text: str) -> Generator[list[str], None, None]:
    """Load issue data from CSV text"""
    reader = csv.reader(io.StringIO(csv_text))
    for row in reader:
        if not row:
            continue
        yield row


def build_command(
    repo: str, title: str, body: str, milestone: str, project: str
) -> Command:
    """Build command to create an issue with GitHub CLI"""
    return (
        "gh",
        [
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body",
            body,
            "--milestone",
            milestone,
            "--project",
            project,
        ],
    )


async def run_all(commands: list[Command]):
    """Run multiple commands"""
    for coro in asyncio.as_completed([run(command) for command in commands]):
        stdout, stderr = await coro
        print(stdout.rstrip())
        if stderr:
            print(stderr.rstrip(), file=sys.stderr)


async def run(command: Command) -> CommandOutput:
    """Run a subprocess"""
    program, args = command
    print(program, *args)
    proc = await create_subprocess_exec(program, *args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await proc.communicate()
    await proc.wait()

    return stdout.decode(), stderr.decode()


if __name__ == "__main__":
    asyncio.run(main())
    
