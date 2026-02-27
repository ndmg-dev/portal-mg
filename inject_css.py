import re

new_css = """/* ========================================
   SCROLLER DE PREVIEWS
   ======================================== */
.scroller-section {
    padding: var(--spacing-2xl) 0;
    background: linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    overflow: hidden;
    position: relative;
}

/* Subtle gradient mask to fade the edges of the scroller */
.scroller-section::before,
.scroller-section::after {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    width: 15%;
    z-index: 2;
    pointer-events: none;
}
.scroller-section::before {
    left: 0;
    background: linear-gradient(to right, var(--bg-secondary) 0%, transparent 100%);
}
.scroller-section::after {
    right: 0;
    background: linear-gradient(to left, var(--bg-secondary) 0%, transparent 100%);
}

.scroller-container {
    max-width: 1400px;
    margin: 0 auto;
    text-align: center;
}

.scroller-titulo {
    font-family: var(--font-heading);
    font-size: var(--text-3xl);
    font-weight: var(--font-bold);
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
}

.scroller-subtitle {
    font-size: var(--text-lg);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xl);
}

.scroller-wrapper {
    width: 100%;
    overflow: hidden;
}

.scroller-track {
    display: flex;
    gap: var(--spacing-lg);
    width: max-content;
    animation: scroll 40s linear infinite;
}

.scroller-track:hover {
    animation-play-state: paused;
}

.scroller-group {
    display: flex;
    gap: var(--spacing-lg);
    padding-right: var(--spacing-lg); /* Ensure gap between group 1 and 2 */
}

.scroller-item {
    flex: 0 0 auto;
    width: 450px;
    height: 280px;
    border-radius: var(--border-radius-xl);
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    background-color: var(--bg-card);
}

.scroller-item::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.1);
    pointer-events: none;
}

.scroller-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top;
    transition: transform 0.6s ease;
}

.scroller-item:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8), 0 0 0 1px var(--accent-yellow);
    z-index: 10;
}

.scroller-item:hover .scroller-img {
    transform: scale(1.05);
}

@keyframes scroll {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .scroller-item {
        width: 300px;
        height: 190px;
    }
}
"""

try:
    with open('static/css/styles.css', 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to replace from /* ==== EQUIPE ... */ down to right before /* ==== RODAPÉ ... */
    # We'll use a positive lookahead to preserve the Rodapé header.
    pattern = r'/\* ========================================\s+EQUIPE \(TEAM MEMBERS\)\s+======================================== \*/.*?/\* ========================================\s+RODAPÉ\s+======================================== \*/'
    
    if re.search(pattern, content, flags=re.DOTALL):
        new_content = re.sub(pattern, new_css + "\n/* ========================================\n   RODAPÉ\n   ======================================== */", content, flags=re.DOTALL)
        
        with open('static/css/styles.css', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("CSS successfully replaced.")
    else:
        print("Pattern not found. Appending to end instead or maybe already replaced.")
        with open('static/css/styles.css', 'a', encoding='utf-8') as f:
            f.write("\n" + new_css)
except Exception as e:
    print(f"Error: {e}")
