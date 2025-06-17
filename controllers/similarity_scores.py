from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_similarity_multi_source(project, projects, college_ideas, team_projects):
    """
    Calculate similarity against multiple data sources.
    Returns list of (source_type, title, similarity_score) tuples.
    """
    proj_txt = f"{project.title} {project.description}"
    all_texts = []
    sources = []
    
    # Add projects from Project table
    for p in projects:
        all_texts.append(f"{p.title} {p.description}")
        sources.append(("Project", p.title))
    
    # Add college ideas from CollegeIdeas table
    for ci in college_ideas:
        all_texts.append(f"{ci.title} {ci.description}")
        sources.append(("College Idea", ci.title))
    
    # Add team projects from TeamProject table
    for tp in team_projects:
        all_texts.append(f"{tp.title} {tp.description}")
        sources.append(("Team Project", tp.title))
    
    # Handle case when no existing projects
    if not all_texts:
        return []
    
    try:
        # Calculate TF-IDF and cosine similarity
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 2)
        )
        tfidf_matrix = vectorizer.fit_transform([proj_txt] + all_texts)
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        
        # Return results with source information
        return [
            (sources[i][0], sources[i][1], float(score)) 
            for i, score in enumerate(similarity_matrix[0])
        ]
        
    except Exception as e:
        print(f"Error in similarity calculation: {e}")
        return []