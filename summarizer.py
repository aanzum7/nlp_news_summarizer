import streamlit as st  # type: ignore
import pandas as pd  # type: ignore
import ast

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="NovelNexus | Premium Bookstore", page_icon="📚", layout="wide")

# Safe State Initialization (Ensures no structural type mismatches)
if "selected_isbn" not in st.session_state:
    st.session_state.selected_isbn = None

if "reading_list" not in st.session_state or not isinstance(st.session_state.reading_list, set):
    # Auto-migrate older list sessions seamlessly to set structure
    if "reading_list" in st.session_state and isinstance(st.session_state.reading_list, list):
        st.session_state.reading_list = set(st.session_state.reading_list)
    else:
        st.session_state.reading_list = set()

# ---------------------------
# Global Design Theme & Styles
# ---------------------------
CONFIG = {
    "background_color": "#0F1115",
    "card_bg": "#1A1D24",
    "card_border": "#2D3139",
    "text_color": "#E1E4EA",
    "accent_color": "#4F46E5",  
    "success_color": "#10B981",
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
}

st.markdown(f"""
<style>
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {CONFIG['background_color']};
        font-family: {CONFIG['font_family']};
        color: {CONFIG['text_color']};
    }}
    
    /* Premium Book Store Card Design */
    .book-card {{
        background: {CONFIG['card_bg']};
        border: 1px solid {CONFIG['card_border']};
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        height: 380px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}
    .book-card:hover {{
        transform: translateY(-6px);
        box-shadow: 0 20px 30px -10px rgba(79, 70, 229, 0.3);
        border-color: {CONFIG['accent_color']};
    }}
    .book-title {{
        font-size: 14px;
        font-weight: 700;
        color: #FFFFFF;
        margin: 10px 0 2px 0;
        line-height: 1.3;
        min-height: 38px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-align: left;
    }}
    .book-meta {{
        font-size: 12px;
        color: #9CA3AF;
        margin: 2px 0;
        text-align: left;
        display: flex;
        align-items: center;
        gap: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .star-rating {{
        color: #F59E0B;
        font-size: 11px;
        margin: 4px 0;
        text-align: left;
        width: 100%;
        font-weight: 600;
    }}
    
    .badge-pill {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 30px;
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }}
    .badge-vintage {{ background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.25); }}
    .badge-modern {{ background: rgba(59, 130, 246, 0.15); color: #3B82F6; border: 1px solid rgba(59, 130, 246, 0.25); }}
    
    .info-container {{
        background: #1A1D24;
        border: 1px solid #2D3139;
        border-radius: 10px;
        padding: 16px;
        text-align: left;
        margin-bottom: 14px;
    }}
    .info-label {{
        font-size: 11px;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }}
    .info-value {{
        font-size: 18px;
        font-weight: 600;
        color: #FFFFFF;
        margin-top: 4px;
    }}

    /* AI Crash Terminal Style */
    .terminal-card {{
        background: #1E1E24;
        border-left: 4px solid #EF4444;
        padding: 15px;
        border-radius: 6px;
        font-family: monospace;
        color: #F87171;
        margin: 15px 0;
    }}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Humorous Exception Handler UI Component
# ---------------------------
def show_witty_error(err_message, feature_context="System Core"):
    st.markdown(f"""
    <div class="terminal-card">
        🚨 <b>[AI Engine Outage Status: Roadtrip Pitstop]</b><br>
        <span style="color:#A1A1AA;">Context: Processing {feature_context}</span><br><br>
        <i>"Whoops! The recommendation models just pulled over at a highway diner for a shot of pure espresso. 
        While our matrix vectors stretch their legs, here is the diagnostic telemetry:"</i>
        <br><br>
        <code style="background:#111827; padding:4px 8px; border-radius:4px; color:#FCA5A5;">
            {str(err_message)}
        </code>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------
# High Efficiency Cached Data Engine
# ---------------------------
@st.cache_data(ttl=3600, max_entries=5)
def load_data():
    try:
        user_combined_recommendations = pd.read_csv("data/recommender_result/user_combined_recommendations.csv")
        book_data = pd.read_parquet("data/preprocessed_files/distinct_books.parquet")
        book_similarities = pd.read_csv("data/recommender_result/book_similarities.csv")
    except Exception:
        user_combined_recommendations = pd.DataFrame({
            'user_id': [1001, 1002, 1003],
            'geographic_recommendation': ["['0345339681', '0449212602']", "[]", "[]"],
            'demographic_recommendation': ["['0449212602', '0345339681']", "['0449212602']", "[]"],
            'collaborative_cluster_recommendation': ["['0345339681', '0449212602']", "[]", "[]"]
        })
        book_data = pd.DataFrame({
            'isbn': ['0345339681', '0449212602'], 
            'book_title': ['The Hobbit', 'The Handmaid\'s Tale'], 
            'book_author': ['J.R.R. Tolkien', 'Margaret Atwood'],
            'publisher': ['Ballantine Books', 'Fawcett Books'], 
            'year_of_publication': [1986, 1998], 
            'image_url': ['https://images.amazon.com/images/P/0345339681.01.MZZZZZZZ.jpg', 'https://images.amazon.com/images/P/0449212602.01.MZZZZZZZ.jpg']
        })
        book_similarities = pd.DataFrame({'isbn': ['0345339681', '0449212602'], 'similar_books': ['0449212602', '0345339681']})
    
    if 'year_of_publication' in book_data.columns:
        book_data['year_of_publication'] = pd.to_numeric(book_data['year_of_publication'], errors='coerce').fillna(0).astype(int)
        
    return user_combined_recommendations, book_data, book_similarities

user_info, book_data, book_similarities = load_data()

# Pre-compiled high speed dictionaries for O(1) matching performance
@st.cache_resource
def build_lookups(_book_data, _book_similarities):
    book_dict = _book_data.set_index('isbn').to_dict(orient='index')
    similarity_dict = _book_similarities.set_index('isbn')['similar_books'].to_dict()
    return book_dict, similarity_dict

BOOK_LOOKUP, SIMILARITY_LOOKUP = build_lookups(book_data, book_similarities)

# ---------------------------
# Optimised Light Helpers
# ---------------------------
def convert_to_list(value):
    if not isinstance(value, str): return value or []
    value = value.strip()
    if not value: return []
    try:
        return ast.literal_eval(value)
    except:
        try:
            return ast.literal_eval(value.replace("'", '"'))
        except:
            return []

def get_similar_books_fast(isbn):
    similar_isbns = SIMILARITY_LOOKUP.get(isbn, "")
    if isinstance(similar_isbns, str) and similar_isbns:
        return [x.strip() for x in similar_isbns.split(",")][:10]
    return []

def get_book_details_fast(isbns):
    records = []
    for i in isbns:
        str_i = str(i)
        if str_i in BOOK_LOOKUP:
            item = BOOK_LOOKUP[str_i].copy()
            item['isbn'] = str_i
            records.append(item)
    return pd.DataFrame(records)

# ---------------------------
# UI Fragment - Isolated Rerenders 
# ---------------------------
@st.fragment
def display_book_cards_grid(book_details, prefix="default", search_term="", year_range=None):
    try:
        if book_details.empty:
            st.markdown("<div style='padding:20px; background:#1A1D24; border-radius:10px; border:1px dashed #2D3139; text-align:center; color:#9CA3AF;'>Shelf empty.</div>", unsafe_allow_html=True)
            return
            
        filtered_df = book_details.copy()
        if search_term:
            filtered_df = filtered_df[
                filtered_df['book_title'].str.contains(search_term, case=False, na=False) |
                filtered_df['book_author'].str.contains(search_term, case=False, na=False)
            ]
            
        if year_range:
            filtered_df = filtered_df[
                (filtered_df['year_of_publication'] >= year_range[0]) &
                (filtered_df['year_of_publication'] <= year_range[1])
            ]

        if filtered_df.empty:
            st.markdown("<div style='padding:20px; background:#1A1D24; border-radius:10px; border:1px dashed #2D3139; text-align:center; color:#9CA3AF;'>No matching items found on this row.</div>", unsafe_allow_html=True)
            return

        cols = st.columns(5)
        for index, (_, book) in enumerate(filtered_df.iterrows()):
            col = cols[index % 5]
            with col:
                isbn = book.get('isbn', 'N/A')
                image_url = book.get('image_url', 'https://via.placeholder.com/150')
                book_title = book.get('book_title', 'Untitled')
                book_author = book.get('book_author', 'Unknown Author')
                publisher = book.get('publisher', 'Unknown Publisher')
                year = book.get('year_of_publication', 0)
                
                badge_html = '<span class="badge-pill badge-vintage">⏳ Vintage</span>' if year < 2000 else '<span class="badge-pill badge-modern">✨ Modern</span>'
                
                # Bulletproof structural set checks
                is_saved = isinstance(st.session_state.reading_list, set) and isbn in st.session_state.reading_list
                fav_icon = "❤️" if is_saved else "🤍"

                st.markdown(f"""
                <div class="book-card">
                    <img src="{image_url}" loading="lazy" style="width: 105px; height: 145px; object-fit: cover; border-radius: 6px; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.4));">
                    <div style="width:100%;">
                        <div class="book-title" title="{book_title}">{book_title}</div>
                        <div class="book-meta" title="{book_author}">✍️ <b>{book_author}</b></div>
                        <div class="star-rating">⭐ 4.6 <span style="color:#6B7280; font-size:10px; font-weight:normal;">(410)</span></div>
                        <div class="book-meta" title="{publisher}">🏢 <small>{publisher}</small></div>
                        <div class="book-meta">📅 <small>Year: {year if year > 0 else 'N/A'}</small></div>
                        <div style="text-align: left; width: 100%; margin-top: 6px;">{badge_html}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                btn_col1, btn_col2 = st.columns([5, 3])
                with btn_col1:
                    if st.button("📖 Open", key=f"det_{prefix}_{isbn}_{index}", use_container_width=True):
                        st.session_state.selected_isbn = isbn
                        st.rerun()
                with btn_col2:
                    if st.button(fav_icon, key=f"save_{prefix}_{isbn}_{index}", use_container_width=True):
                        # Force structural conversion if it ever corrupts dynamically
                        if not isinstance(st.session_state.reading_list, set):
                            st.session_state.reading_list = set(st.session_state.reading_list)
                            
                        if not is_saved:
                            st.session_state.reading_list.add(isbn)
                            st.toast(f"Added to favorites!", icon="❤️")
                        else:
                            st.session_state.reading_list.remove(isbn)
                            st.toast("Removed from favorites.", icon="🗑️")
                        st.rerun()
    except Exception as e:
        show_witty_error(e, feature_context=f"Grid Showcase Layout ({prefix})")

# ---------------------------
# Individual Detailed View Screen
# ---------------------------
def display_book_details_view(isbn):
    try:
        if st.button("← Back to Marketplace Home", use_container_width=True):
            st.session_state.selected_isbn = None
            st.rerun()
            
        if isbn in BOOK_LOOKUP:
            book = BOOK_LOOKUP[isbn]
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(book['image_url'], use_container_width=True)
            with col2:
                st.title(book['book_title'])
                st.markdown(f"### By **{book['book_author']}**")
                
                st.markdown(f"""
                <div class="info-container">
                    <div class="info-label">Publisher</div>
                    <div class="info-value">{book['publisher']}</div>
                </div>
                <div class="info-container">
                    <div class="info-label">Publication Year</div>
                    <div class="info-value">{book['year_of_publication']}</div>
                </div>
                <div class="info-container" style="border-left: 4px solid {CONFIG['success_color']};">
                    <div class="info-label" style="color: {CONFIG['success_color']};">Availability</div>
                    <div class="info-value" style="color: #FFF;">In Stock <span style="font-size:13px; color:#9CA3AF;">(Dispatches within 24 hours)</span></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("✨ Readers Who Bought This Also Enjoyed")
            similar_isbns = get_similar_books_fast(isbn)
            if similar_isbns:
                display_book_cards_grid(get_book_details_fast(similar_isbns), prefix="similar")
            else:
                st.caption("No matches found.")
    except Exception as e:
        show_witty_error(e, feature_context="Item Detailed Description Stage")

# ---------------------------
# Sidebar Frame With Fixed Bottom Dynamic Profiles
# ---------------------------
with st.sidebar:
    st.markdown("<h2 style='color:#FFF; margin-bottom:0;'>📚 NovelNexus</h2>", unsafe_allow_html=True)
    st.caption("Your Premium AI Bookstore")
    st.markdown("---")
    
    # Render count safely regardless of object state types
    saved_count = len(st.session_state.reading_list) if isinstance(st.session_state.reading_list, (set, list)) else 0
    st.metric(label="Active Session Saved Items", value=saved_count)
    
    st.markdown("---")
    st.title("👨‍💻 About the Author")
    st.caption("Tanvir Anzum – AI & Data Researcher")
    st.markdown("""
        <div style='font-size: 14px; font-weight: normal;'>
        Passionate about turning <strong>data into insights</strong> and building <strong>AI-powered tools</strong> for real-world impact.
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='font-size: 14px; font-weight: normal;'>
        <br>
        <a href="https://www.linkedin.com/in/aanzum" target="_blank">
            <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" width="16" style="vertical-align:middle; margin-right:6px;">
            <strong>LinkedIn</strong>
        </a>
        &nbsp;&nbsp;
        <a href="https://www.researchgate.net/profile/Tanvir-Anzum" target="_blank">
            <img src="https://upload.wikimedia.org/wikipedia/commons/5/5e/ResearchGate_icon_SVG.svg" alt="ResearchGate" width="16" style="vertical-align:middle; margin-right:6px;">
            <strong>Research</strong>
        </a>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

# ---------------------------
# Main Routing Logic
# ---------------------------
if st.session_state.selected_isbn:
    display_book_details_view(st.session_state.selected_isbn)
else:
    st.title("📚 Discovery Marketplace")
    
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        global_search = st.text_input("🔍 Search entire catalog...", placeholder="Type title, author or keywords to dynamically filter shelves below...")
    with h_col2:
        user_ids = user_info['user_id'].unique() if 'user_id' in user_info.columns else [1001]
        user_id = st.selectbox("🎯 Active Personalization Profile:", user_ids)
        
    # Guard against completely corrupted/empty data indices
    if 'user_id' in user_info.columns and not user_info[user_info['user_id'] == user_id].empty:
        user_row = user_info[user_info['user_id'] == user_id].iloc[0]
    else:
        user_row = pd.Series({'collaborative_cluster_recommendation': "[]", 'demographic_recommendation': "[]", 'geographic_recommendation': "[]"})
        
    st.markdown("---")
    
    tab_all, tab1, tab2, tab3, tab_saved = st.tabs([
        "📚 All Books", 
        "🤝 Handpicked For You", 
        "👥 Popular Among Peers", 
        "📍 Trending In Your Area",
        f"❤️ My Favorites ({saved_count})"
    ])
    
    # 1. CATEGORY VIEW FIRST
    with tab_all:
        st.markdown("### Browse Categories")
        st.markdown("#### ⏳ Vintage Classics (Published Before 2000)")
        vintage_books = book_data[book_data['year_of_publication'] < 2000] if 'year_of_publication' in book_data.columns else book_data
        display_book_cards_grid(vintage_books[:10], prefix="all_vintage", search_term=global_search)
        
        st.markdown("---")
        st.markdown("#### ✨ Modern Era Hits (Published 2000 & Later)")
        modern_books = book_data[book_data['year_of_publication'] >= 2000] if 'year_of_publication' in book_data.columns else book_data
        display_book_cards_grid(modern_books[:10], prefix="all_modern", search_term=global_search)
        
    # 2. PERSONALIZED RECOMMENDATIONS
    with tab1:
        st.markdown("### Handpicked For You")
        collab_ids = convert_to_list(user_row.get('collaborative_cluster_recommendation', "[]"))[:10]
        display_book_cards_grid(get_book_details_fast(collab_ids), prefix="curated", search_term=global_search)
        
    with tab2:
        st.markdown("### Peer Demographic Trends")
        demo_ids = convert_to_list(user_row.get('demographic_recommendation', "[]"))[:10]
        display_book_cards_grid(get_book_details_fast(demo_ids), prefix="demographic", search_term=global_search)
        
    with tab3:
        st.markdown("### Regional Best Sellers")
        geo_ids = convert_to_list(user_row.get('geographic_recommendation', "[]"))[:10]
        display_book_cards_grid(get_book_details_fast(geo_ids), prefix="geographic", search_term=global_search)

    # 3. SAVED USER REPOSITORY
    with tab_saved:
        st.markdown("### Your Favorites Vault")
        if st.session_state.reading_list:
            if st.button("🗑️ Clear Entire List", use_container_width=True):
                st.session_state.reading_list.clear()
                st.rerun()
            saved_books = get_book_details_fast(list(st.session_state.reading_list))
            display_book_cards_grid(saved_books, prefix="vault")
        else:
            st.info("Your favorites vault is empty.")
