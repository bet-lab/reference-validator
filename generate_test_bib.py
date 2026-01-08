import random

# Extended Real world sample data
# Format: (key, type, fields_dict)
base_entries = [
    # --- CS / ML ---
    (
        "vaswani2017attention",
        "inproceedings",
        {
            "author": "Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N and Kaiser, {\L}ukasz and Polosukhin, Illia",
            "title": "Attention is all you need",
            "booktitle": "Advances in neural information processing systems",
            "pages": "5998--6008",
            "year": "2017",
            "url": "https://proceedings.neurips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html",
        },
    ),
    (
        "he2016deep",
        "inproceedings",
        {
            "author": "He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian",
            "title": "Deep residual learning for image recognition",
            "booktitle": "Proceedings of the IEEE conference on computer vision and pattern recognition",
            "pages": "770--778",
            "year": "2016",
            "doi": "10.1109/CVPR.2016.90",
        },
    ),
    (
        "silver2016mastering",
        "article",
        {
            "author": "Silver, David and Huang, Aja and Maddison, Chris J and Guez, Arthur and Sifre, Laurent and Van Den Driessche, George and Schrittwieser, Julian and Antonoglou, Ioannis and Panneershelvam, Veda and Lanctot, Marc and others",
            "title": "Mastering the game of Go with deep neural networks and tree search",
            "journal": "Nature",
            "volume": "529",
            "number": "7587",
            "pages": "484--489",
            "year": "2016",
            "doi": "10.1038/nature16961",
        },
    ),
    # --- Physics ---
    (
        "aad2012observation",
        "article",
        {
            "author": "Aad, Georges and Abajyan, T and Abbott, B and Abdallah, J and Abdel Khalek, S and Abdelalim, AA and Abdinov, O and Aben, R and Abi, B and Abolins, M and others",
            "title": "Observation of a new particle in the search for the Standard Model Higgs boson with the ATLAS detector at the LHC",
            "journal": "Physics Letters B",
            "volume": "716",
            "number": "1",
            "pages": "1--29",
            "year": "2012",
            "doi": "10.1016/j.physletb.2012.08.020",
        },
    ),
    (
        "einstein1935can",
        "article",
        {
            "author": "Einstein, Albert and Podolsky, Boris and Rosen, Nathan",
            "title": "Can quantum-mechanical description of physical reality be considered complete?",
            "journal": "Physical review",
            "volume": "47",
            "number": "10",
            "pages": "777",
            "year": "1935",
            "doi": "10.1103/PhysRev.47.777",
        },
    ),
    # --- Biology / Medicine ---
    (
        "watson1953molecular",
        "article",
        {
            "author": "Watson, James D and Crick, Francis HC",
            "title": "Molecular structure of nucleic acids: a structure for deoxyribose nucleic acid",
            "journal": "Nature",
            "volume": "171",
            "number": "4356",
            "pages": "737--738",
            "year": "1953",
            "doi": "10.1038/171737a0",
        },
    ),
    (
        "varmus1989retroviruses",
        "book",
        {
            "author": "Varmus, Harold and Brown, Patrick",
            "title": "Retroviruses",
            "publisher": "Cold Spring Harbor Laboratory Press",
            "year": "1989",
            "address": "Cold Spring Harbor, NY",
        },
    ),
    # --- Chemistry ---
    (
        "sharpless2001click",
        "article",
        {
            "author": "Kolb, Hartmuth C and Finn, MG and Sharpless, K Barry",
            "title": "Click chemistry: diverse chemical function from a few good reactions",
            "journal": "Angewandte Chemie International Edition",
            "volume": "40",
            "number": "11",
            "pages": "2004--2021",
            "year": "2001",
            "doi": "10.1002/1521-3773(20010601)40:11<2004::AID-ANIE2004>3.0.CO;2-5",
        },
    ),
    # --- Economics ---
    (
        "kahneman1979prospect",
        "article",
        {
            "author": "Kahneman, Daniel and Tversky, Amos",
            "title": "Prospect theory: An analysis of decision under risk",
            "journal": "Econometrica",
            "volume": "47",
            "number": "2",
            "pages": "263--291",
            "year": "1979",
            "doi": "10.2307/1914185",
        },
    ),
    (
        "nash1950equilibrium",
        "article",
        {
            "author": "Nash, John F",
            "title": "Equilibrium points in n-person games",
            "journal": "Proceedings of the national academy of sciences",
            "volume": "36",
            "number": "1",
            "pages": "48--49",
            "year": "1950",
        },
    ),
    # --- Books ---
    (
        "knuth1984texbook",
        "book",
        {
            "author": "Knuth, Donald E",
            "title": "The TeXbook",
            "publisher": "Addison-Wesley",
            "year": "1984",
            "address": "Reading, Massachusetts",
        },
    ),
    (
        "feynman1963lectures",
        "book",
        {
            "author": "Feynman, Richard P and Leighton, Robert B and Sands, Matthew",
            "title": "The Feynman lectures on physics",
            "publisher": "Addison-Wesley",
            "year": "1963",
            "volume": "1",
        },
    ),
    # --- Misc / ArXiv ---
    (
        "kingma2014adam",
        "misc",
        {
            "author": "Kingma, Diederik P and Ba, Jimmy",
            "title": "Adam: A method for stochastic optimization",
            "year": "2014",
            "eprint": "1412.6980",
            "archivePrefix": "arXiv",
            "primaryClass": "cs.LG",
        },
    ),
    (
        "perelman2002entropy",
        "misc",
        {
            "author": "Perelman, Grisha",
            "title": "The entropy formula for the Ricci flow and its geometric applications",
            "year": "2002",
            "eprint": "math/0211159",
            "archivePrefix": "arXiv",
            "primaryClass": "math.DG",
        },
    ),
    # --- Tech Reports ---
    (
        "brin1998anatomy",
        "techreport",
        {
            "author": "Brin, Sergey and Page, Lawrence",
            "title": "The anatomy of a large-scale hypertextual web search engine",
            "institution": "Stanford University",
            "year": "1998",
        },
    ),
    # --- Theses ---
    (
        "shannon1940symbolic",
        "mastersthesis",
        {
            "author": "Shannon, Claude Elwood",
            "title": "A symbolic analysis of relay and switching circuits",
            "school": "Massachusetts Institute of Technology",
            "year": "1940",
        },
    ),
    (
        "curie1903recherches",
        "phdthesis",
        {
            "author": "Curie, Marie",
            "title": "Recherches sur les substances radioactives",
            "school": "Sorbonne",
            "year": "1903",
        },
    ),
    # --- Patents ---
    (
        "google2001pagerank",
        "misc",
        {
            "author": "Page, Lawrence",
            "title": "Method for node ranking in a linked database",
            "year": "2001",
            "note": "US Patent 6,285,999",
        },
    ),
]


# Advanced Mutations
def mutate_strip_year(fields):
    f = fields.copy()
    if "year" in f:
        del f["year"]
    return f, "error", "missing_year"


def mutate_strip_pages(fields):
    f = fields.copy()
    if "pages" in f:
        del f["pages"]
    return f, "error" if "pages" in fields else "neutral", "missing_pages"


def mutate_strip_journal(fields):
    f = fields.copy()
    if "journal" in f:
        del f["journal"]
    return f, "error" if "journal" in fields else "neutral", "missing_journal"


def mutate_strip_publisher(fields):
    f = fields.copy()
    if "publisher" in f:
        del f["publisher"]
    return f, "neutral", "missing_publisher_lx"


def mutate_strip_volume(fields):
    f = fields.copy()
    if "volume" in f:
        del f["volume"]
    return f, "warning", "missing_volume"


def mutate_add_junk(fields):
    f = fields.copy()
    f["junk_field"] = "This should be ignored"
    return f, "neutral", "junk_added"


def mutate_latex_accent(fields):
    f = fields.copy()
    if "author" in f:
        f["author"] = f["author"].replace("e", "{\\'e}").replace("o", '{\\"o}')
    return f, "neutral", "latex_accents"


def mutate_valid(fields):
    return fields.copy(), "success", "clean"


mutations_map = {
    "article": [
        mutate_valid,
        mutate_valid,
        mutate_strip_journal,
        mutate_strip_year,
        mutate_strip_volume,
        mutate_latex_accent,
    ],
    "inproceedings": [
        mutate_valid,
        mutate_valid,
        mutate_strip_pages,
        mutate_strip_year,
        mutate_add_junk,
        mutate_latex_accent,
    ],
    "book": [mutate_valid, mutate_strip_publisher, mutate_strip_year],
    "misc": [mutate_valid, mutate_strip_year, mutate_add_junk],
    "mastersthesis": [mutate_valid, mutate_strip_year],
    "phdthesis": [mutate_valid, mutate_strip_year],
    "techreport": [mutate_valid, mutate_strip_year],
}

full_bib = []
count = 0
target_count = 100

while count < target_count:
    # Pick a base
    base_key, b_type, b_fields = random.choice(base_entries)

    # Pick a mutation
    possible_muts = mutations_map.get(b_type, [mutate_valid])
    mutation = random.choice(possible_muts)

    new_fields, expectation, tag = mutation(b_fields)

    # Create unique key with occasional duplicates?
    # No, duplicates usually crash or overwrite parser usually, but validator might handle.
    # Let's keep keys unique for now to ensure 100 entries.
    new_key = f"{base_key}_{tag}_{count}"

    entry_str = f"@{b_type}{{{new_key},\n"
    for k, v in new_fields.items():
        entry_str += f"  {k} = {{{v}}},\n"
    entry_str += "}\n"

    full_bib.append(entry_str)
    count += 1

with open("comprehensive_test.bib", "w", encoding="utf-8") as f:
    f.write("\n".join(full_bib))

print(f"Generated {len(full_bib)} entries in comprehensive_test.bib")
