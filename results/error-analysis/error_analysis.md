# Query-level error analysis

> Every example below is drawn from real `results/runs/*.json` data against real `qrels_test.json` relevance judgments. Rank thresholds: good <= 10, bad = None (not retrieved in top 100) or > 50.

## BM25 wins / MedCPT loses (52 found, showing top 5)

**Query `PLAIN-2490`:** The Actual Benefit of Diet vs. Drugs
- Relevant doc `MED-2111` (relevance=1): *Updating a 12-year experience with arrest and reversal therapy for coronary heart disease (an overdue requiem for palliative cardiology).*
  > Coronary artery disease is essentially nonexistent in cultures whose nutrition assures cholesterol levels <150 mg/dl. Patients with advanced coronary artery disease may abolish disease progression through a plant-based...
- Ranks: tfidf=-, bm25=1, bge=-, medcpt=-, hybrid_rrf=7, hybrid_reranked=20

**Query `PLAIN-227`:** Increasing Muscle Strength with Fenugreek
- Relevant doc `MED-4150` (relevance=1): *Pseudo-maple syrup urine disease due to maternal prenatal ingestion of fenugreek.*
  > Fenugreek, maple syrup and the urine of maple syrup urine disease (MSUD) patients all share a characteristic odour originating from a common component, sotolone. Ingestion of fenugreek by mothers during labour resulted...
- Ranks: tfidf=1, bm25=2, bge=29, medcpt=-, hybrid_rrf=12, hybrid_reranked=3

**Query `PLAIN-2040`:** salmon
- Relevant doc `MED-3024` (relevance=1): *Dietary lipids modulate methylmercury toxicity in Atlantic salmon.*
  > This experiment aimed to study the molecular toxicity of methylmercury (MeHg) in liver, brain and white muscle of Atlantic salmon fed a diet based on fish oil (FO, high dietary n-3/n-6 ratio) compared to an alternative...
- Ranks: tfidf=3, bm25=2, bge=2, medcpt=-, hybrid_rrf=8, hybrid_reranked=6

**Query `PLAIN-531`:** alternative medicine
- Relevant doc `MED-4374` (relevance=1): *Health food store recommendations for breast cancer patients.*
  > CONTEXT: Despite cancer patients' widespread and growing use of complementary and alternative medicine, minimal attention has been paid to the role of health food stores in the "supply side" of this phenomenon....
- Ranks: tfidf=11, bm25=3, bge=13, medcpt=-, hybrid_rrf=20, hybrid_reranked=2

**Query `PLAIN-33`:** What’s Driving America’s Obesity Problem?
- Relevant doc `MED-2715` (relevance=2): *Physical activity energy expenditure has not declined since the 1980s and matches energy expenditures of wild mammals.*
  > OBJECTIVE: Obesity results from protracted energy imbalance. Whether this comprises excessive energy intake, lowered physical activity or both, remains disputed. DESIGN: Physical activity energy expenditure, evaluated...
- Ranks: tfidf=2, bm25=4, bge=86, medcpt=-, hybrid_rrf=35, hybrid_reranked=20

## MedCPT wins / BM25 loses (244 found, showing top 5)

**Query `PLAIN-12`:** Exploiting Autophagy to Live Longer
- Relevant doc `MED-2514` (relevance=1): *Why human lifespan is rapidly increasing: solving "longevity riddle" with "revealed-slow-aging" hypothesis*
  > Healthy life span is rapidly increasing and human aging seems to be postponed. As recently exclaimed in Nature, these findings are so perplexing that they can be dubbed the 'longevity riddle'. To explain current...
- Ranks: tfidf=-, bm25=-, bge=5, medcpt=1, hybrid_rrf=10, hybrid_reranked=3

**Query `PLAIN-33`:** What’s Driving America’s Obesity Problem?
- Relevant doc `MED-2722` (relevance=1): *Prevalence of physical activity and obesity in US counties, 2001–2011: a road map for action*
  > Background Obesity and physical inactivity are associated with several chronic conditions, increased medical care costs, and premature death. Methods We used the Behavioral Risk Factor Surveillance System (BRFSS), a...
- Ranks: tfidf=-, bm25=-, bge=4, medcpt=1, hybrid_rrf=27, hybrid_reranked=8

**Query `PLAIN-133`:** Starving Tumors of Their Blood Supply
- Relevant doc `MED-3550` (relevance=2): *Tumor Angiogenesis as a Target for Dietary Cancer Prevention*
  > Between 2000 and 2050, the number of new cancer patients diagnosed annually is expected to double, with an accompanying increase in treatment costs of more than $80 billion over just the next decade. Efficacious...
- Ranks: tfidf=-, bm25=-, bge=9, medcpt=1, hybrid_rrf=16, hybrid_reranked=5

**Query `PLAIN-291`:** Stool Size and Breast Cancer Risk
- Relevant doc `MED-4641` (relevance=1): *Cytological abnormalities in nipple aspirates of breast fluid from women with severe constipation.*
  > The relation between epithelial dysplasia in nipple aspirates of breast fluid and frequency of bowel movements was studied in 1481 white women. There was a significant positive association with dysplasia (risk ratio...
- Ranks: tfidf=-, bm25=-, bge=5, medcpt=1, hybrid_rrf=28, hybrid_reranked=6

**Query `PLAIN-344`:** Dioxins Stored in Our Own Fat May Increase Diabetes Risk
- Relevant doc `MED-2394` (relevance=2): *Molecular Epidemiologic Evidence for Diabetogenic Effects of Dioxin Exposure in U.S. Air Force Veterans of the Vietnam War*
  > Background One of the outcomes positively associated with dioxin exposure in humans is type 2 diabetes. Objectives This study was conducted in order to find the molecular biological evidence for the diabetogenic action...
- Ranks: tfidf=-, bm25=-, bge=2, medcpt=1, hybrid_rrf=22, hybrid_reranked=5

## Hybrid fixes a lexical (BM25) failure (76 found, showing top 5)

**Query `PLAIN-551`:** amnesia
- Relevant doc `MED-4381` (relevance=1): *Amnesic shellfish poison.*
  > Amnesic shellfish poisoning (ASP) is caused by consumption of shellfish that have accumulated domoic acid, a neurotoxin produced by some strains of phytoplankton. The neurotoxic properties of domoic acid result in...
- Ranks: tfidf=-, bm25=-, bge=2, medcpt=1, hybrid_rrf=1, hybrid_reranked=1

**Query `PLAIN-583`:** antinutrients
- Relevant doc `MED-2988` (relevance=1): *The role of phytic acid in legumes: antinutrient or beneficial function?*
  > This review describes the present state of knowledge about phytic acid (phytate), which is often present in legume seeds. The antinutritional effects of phytic acid primarily relate to the strong chelating associated...
- Ranks: tfidf=-, bm25=-, bge=9, medcpt=1, hybrid_rrf=1, hybrid_reranked=1

**Query `PLAIN-817`:** canker sores
- Relevant doc `MED-4841` (relevance=1): *Humoral immunity to cow's milk proteins and gliadin within the etiology of recurrent aphthous ulcers?*
  > OBJECTIVES: The goal of this study was to determine the incidence of serum antibodies to gliadin and to cow's milk proteins (CMP) using ELISA test, within patients who have recurrent aphthous ulcers (RAU). SUBJECTS AND...
- Ranks: tfidf=-, bm25=-, bge=14, medcpt=1, hybrid_rrf=1, hybrid_reranked=21

**Query `PLAIN-1214`:** Fosamax
- Relevant doc `MED-2990` (relevance=1): *Bisphosphonate-associated osteonecrosis of the jaw: report of a task force of the American Society for Bone and Mineral Research.*
  > ONJ has been increasingly suspected to be a potential complication of bisphosphonate therapy in recent years. Thus, the ASBMR leadership appointed a multidisciplinary task force to address key questions related to case...
- Ranks: tfidf=-, bm25=-, bge=-, medcpt=1, hybrid_rrf=1, hybrid_reranked=12

**Query `PLAIN-1867`:** pineapples
- Relevant doc `MED-3744` (relevance=1): *Antioxidant and antiproliferative activities of common fruits.*
  > Consumption of fruits and vegetables has been associated with reduced risk of chronic diseases such as cardiovascular disease and cancer. Phytochemicals, especially phenolics, in fruits and vegetables are suggested to...
- Ranks: tfidf=-, bm25=-, bge=2, medcpt=1, hybrid_rrf=1, hybrid_reranked=1

## Hybrid fixes a semantic (MedCPT) failure (17 found, showing top 5)

**Query `PLAIN-2490`:** The Actual Benefit of Diet vs. Drugs
- Relevant doc `MED-2111` (relevance=1): *Updating a 12-year experience with arrest and reversal therapy for coronary heart disease (an overdue requiem for palliative cardiology).*
  > Coronary artery disease is essentially nonexistent in cultures whose nutrition assures cholesterol levels <150 mg/dl. Patients with advanced coronary artery disease may abolish disease progression through a plant-based...
- Ranks: tfidf=-, bm25=1, bge=-, medcpt=-, hybrid_rrf=7, hybrid_reranked=20

**Query `PLAIN-2040`:** salmon
- Relevant doc `MED-3024` (relevance=1): *Dietary lipids modulate methylmercury toxicity in Atlantic salmon.*
  > This experiment aimed to study the molecular toxicity of methylmercury (MeHg) in liver, brain and white muscle of Atlantic salmon fed a diet based on fish oil (FO, high dietary n-3/n-6 ratio) compared to an alternative...
- Ranks: tfidf=3, bm25=2, bge=2, medcpt=-, hybrid_rrf=8, hybrid_reranked=6

**Query `PLAIN-1151`:** factory farming practices
- Relevant doc `MED-2742` (relevance=1): *Consumer knowledge of foodborne microbial hazards and food-handling practices.*
  > A national telephone survey was conducted of 1,620 randomly selected U.S. residents who spoke English, were at least 18 years old, and resided in households with kitchen facilities. Respondents were interviewed about...
- Ranks: tfidf=6, bm25=7, bge=44, medcpt=98, hybrid_rrf=7, hybrid_reranked=18

**Query `PLAIN-196`:** Should We Avoid Titanium Dioxide?
- Relevant doc `MED-5326` (relevance=1): *Red meat and colon cancer: should we become vegetarians, or can we make meat safer?*
  > The effect of meat consumption on cancer risk is a controversial issue. However, recent meta-analyses show that high consumers of cured meats and red meat are at increased risk of colorectal cancer. This increase is...
- Ranks: tfidf=11, bm25=10, bge=-, medcpt=88, hybrid_rrf=10, hybrid_reranked=10

**Query `PLAIN-2580`:** Academy of Nutrition and Dietetics Conflicts of Interest
- Relevant doc `MED-2725` (relevance=1): *Conflicts of interest in approvals of additives to food determined to be generally recognized as safe: out of balance.*
  > IMPORTANCE: Food and Drug Administration (FDA) guidance allows food manufacturers to determine whether additives to food are "generally recognized as safe" (GRAS). Manufacturers are not required to notify the FDA of a...
- Ranks: tfidf=3, bm25=15, bge=2, medcpt=85, hybrid_rrf=8, hybrid_reranked=5

## Reranker improves the result (926 found, showing top 5)

**Query `PLAIN-2850`:** More Antibiotics In White Meat or Dark Meat?
- Relevant doc `MED-4167` (relevance=1): *Influence of water and food consumption on inadvertent antibiotics intake among general population.*
  > Antibiotic entry into the water environment has been of growing concern. However, few investigations have been performed to examine the potential for indirect human exposure to environmental antibiotic residues. We...
- Ranks: tfidf=31, bm25=-, bge=14, medcpt=10, hybrid_rrf=49, hybrid_reranked=5

**Query `PLAIN-2102`:** smoking
- Relevant doc `MED-3099` (relevance=1): *The aryl hydrocarbon receptor and its xenobiotic ligands: a fundamental trigger for cardiovascular diseases.*
  > This review reconsiders a major cause of cardiovascular diseases, tobacco smoking, as the activation of the Aryl hydrocarbon Receptor (AhR), also known as the dioxin receptor, by aryl hydrocarbons from the tar fraction...
- Ranks: tfidf=52, bm25=47, bge=36, medcpt=84, hybrid_rrf=48, hybrid_reranked=6

**Query `PLAIN-2720`:** Keeping Your Hands Warm With Citrus
- Relevant doc `MED-3469` (relevance=1): *Postprandial glycemic response to orange juice and nondiet cola: is there a difference?*
  > The purpose of this study was to compare the effects of unsweetened fruit juice and regular, decaffeinated soda on postprandial serum glucose levels in individuals with non-insulin-dependent diabetes mellitus (NIDDM)...
- Ranks: tfidf=-, bm25=-, bge=-, medcpt=24, hybrid_rrf=49, hybrid_reranked=8

**Query `PLAIN-44`:** Who Should be Careful About Curcumin?
- Relevant doc `MED-2794` (relevance=1): *Dietary turmeric potentially reduces the risk of cancer.*
  > Turmeric, a plant rhizome that is often dried, ground and used as a cooking spice, has also been used medicinally for several thousand years. Curcumin, the phytochemical that gives turmeric its golden color, is...
- Ranks: tfidf=33, bm25=73, bge=7, medcpt=23, hybrid_rrf=46, hybrid_reranked=6

**Query `PLAIN-33`:** What’s Driving America’s Obesity Problem?
- Relevant doc `MED-2723` (relevance=2): *Health and economic burden of the projected obesity trends in the USA and the UK.*
  > Rising prevalence of obesity is a worldwide health concern because excess weight gain within populations forecasts an increased burden from several diseases, most notably cardiovascular diseases, diabetes, and cancers....
- Ranks: tfidf=-, bm25=-, bge=3, medcpt=10, hybrid_rrf=45, hybrid_reranked=6

## Reranker degrades the result (832 found, showing top 5)

**Query `PLAIN-2408`:** Zoloft
- Relevant doc `MED-1360` (relevance=1): *Exercise and Pharmacotherapy in the Treatment of Major Depressive Disorder*
  > Objective To assess whether patients receiving aerobic exercise training performed either at home or in a supervised group setting achieve reductions in depression comparable to standard antidepressant medication...
- Ranks: tfidf=-, bm25=-, bge=1, medcpt=3, hybrid_rrf=3, hybrid_reranked=50

**Query `PLAIN-1453`:** junk food
- Relevant doc `MED-3091` (relevance=1): *Lack of Awareness among Future Medical Professionals about the Risk of Consuming Hidden Phosphate-Containing Processed Food and Drinks*
  > Phosphate toxicity is an important determinant of mortality in patients with chronic kidney disease (CKD), particularly those undergoing hemodialysis treatments. CKD patients are advised to take a low...
- Ranks: tfidf=71, bm25=43, bge=-, medcpt=9, hybrid_rrf=5, hybrid_reranked=50

**Query `PLAIN-2408`:** Zoloft
- Relevant doc `MED-1357` (relevance=1): *Effects of exercise training on older patients with major depression.*
  > BACKGROUND: Previous observational and interventional studies have suggested that regular physical exercise may be associated with reduced symptoms of depression. However, the extent to which exercise training may...
- Ranks: tfidf=-, bm25=-, bge=8, medcpt=5, hybrid_rrf=5, hybrid_reranked=49

**Query `PLAIN-1635`:** milk
- Relevant doc `MED-2774` (relevance=1): *Milk stimulates growth of prostate cancer cells in culture.*
  > Concern has been expressed about the fact that cows' milk contains estrogens and could stimulate the growth of hormone-sensitive tumors. In this study, organic cows' milk and two commercial substitutes were digested in...
- Ranks: tfidf=1, bm25=5, bge=1, medcpt=12, hybrid_rrf=3, hybrid_reranked=46

**Query `PLAIN-1837`:** pesticides
- Relevant doc `MED-1158` (relevance=1): *Behaviour of some organophosphorus and organochlorine pesticides in potatoes during soaking in different solutions.*
  > The efficiencies of acidic solutions (radish, citric acid, ascorbic acid, acetic acid and hydrogen peroxide), neutral solutions (sodium chloride) and alkaline solution (sodium carbonate) as well as tap water in the...
- Ranks: tfidf=10, bm25=4, bge=15, medcpt=16, hybrid_rrf=6, hybrid_reranked=48

