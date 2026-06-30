// The Geopol Brief — Site App
// Loads briefs from /briefs/ directory

const BRIEFS_DIR = '/briefs/';

async function loadBriefs() {
    try {
        const resp = await fetch(BRIEFS_DIR + 'index.json');
        if (!resp.ok) throw new Error('No index');
        const briefs = await resp.json();
        return briefs;
    } catch (e) {
        console.error('Failed to load briefs:', e);
        return [];
    }
}

async function loadBrief(slug) {
    try {
        const resp = await fetch(BRIEFS_DIR + slug + '.json');
        if (!resp.ok) throw new Error('No brief');
        return await resp.json();
    } catch (e) {
        console.error('Failed to load brief:', slug, e);
        return null;
    }
}

function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatDateShort(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function renderStoryHTML(story) {
    const flagHTML = story.emoji
        ? `<div class="story-flag"><span class="story-emoji">${story.emoji}</span>${story.category ? `<span class="story-category">${story.category}</span>` : ''}</div>`
        : (story.category ? `<div class="story-flag"><span class="story-category">${story.category}</span></div>` : '');

    const sourceHTML = story.source
        ? `<div class="story-source">Source: <a href="${story.source_url || '#'}" target="_blank" rel="noopener">${story.source}</a></div>`
        : '';

    return `
        <div class="story">
            ${flagHTML}
            <div class="story-headline">${story.headline}</div>
            <div class="story-body">${story.body}</div>
            ${sourceHTML}
        </div>
    `;
}

function renderLatestBrief(brief) {
    if (!brief) return '<p>No briefs yet. Check back soon.</p>';

    const tagClass = brief.type === 'morning' ? 'morning' : 'evening';
    const tagLabel = brief.type === 'morning' ? '☀️ Morning Brief' : '🌙 Evening Analysis';
    const standfirst = brief.stories.slice(0, 3).map(s => s.headline).join(' · ');

    return `
        <div class="brief-tag ${tagClass}">${tagLabel}</div>
        <div class="brief-date">${formatDate(brief.date)}</div>
        <h1 class="brief-headline"><a href="/brief.html?b=${brief.slug}">${brief.title}</a></h1>
        <div class="brief-standfirst">${standfirst}</div>
        <div class="brief-stories">
            ${brief.stories.slice(0, 4).map(s => renderStoryHTML(s)).join('')}
        </div>
        <p style="margin-top:1rem;"><a href="/brief.html?b=${brief.slug}" style="font-family:var(--font-body);font-size:0.85rem;letter-spacing:0.05em;text-transform:uppercase;font-weight:600;color:var(--color-link-hover);text-decoration:none;">Read full brief →</a></p>
    `;
}

function renderBriefCard(brief) {
    const tagClass = brief.type === 'morning' ? 'morning' : 'evening';
    const tagLabel = brief.type === 'morning' ? '☀️ Morning' : '🌙 Evening';
    const excerpt = brief.stories.length > 0 ? brief.stories[0].headline : '';

    return `
        <div class="brief-card">
            <div class="brief-card-date">${formatDateShort(brief.date)} · ${tagLabel}</div>
            <div class="brief-card-title"><a href="/brief.html?b=${brief.slug}">${brief.title}</a></div>
            <div class="brief-card-excerpt">${excerpt}</div>
        </div>
    `;
}

async function renderHomePage() {
    const briefs = await loadBriefs();
    if (briefs.length === 0) {
        document.getElementById('latest-brief').innerHTML = '<p>No briefs yet. Check back soon.</p>';
        return;
    }

    // Latest brief (full)
    const latest = briefs[0];
    const latestFull = await loadBrief(latest.slug);
    document.getElementById('latest-brief').innerHTML = renderLatestBrief(latestFull || latest);

    // Recent briefs (cards)
    const recentContainer = document.getElementById('recent-briefs');
    recentContainer.innerHTML = briefs.slice(1, 10)
        .map(b => renderBriefCard(b))
        .join('');
}

async function renderBriefPage() {
    const params = new URLSearchParams(window.location.search);
    const slug = params.get('b');
    if (!slug) {
        window.location.href = '/';
        return;
    }

    const brief = await loadBrief(slug);
    if (!brief) {
        document.querySelector('.article-body').innerHTML = '<p>Brief not found.</p>';
        return;
    }

    const tagClass = brief.type === 'morning' ? 'morning' : 'evening';
    const tagLabel = brief.type === 'morning' ? '☀️ Morning Brief' : '🌙 Evening Analysis';

    document.querySelector('.article-header').innerHTML = `
        <div class="brief-tag ${tagClass}">${tagLabel}</div>
        <div class="brief-date">${formatDate(brief.date)}</div>
        <h1 class="brief-headline">${brief.title}</h1>
        ${brief.standfirst ? `<div class="brief-standfirst">${brief.standfirst}</div>` : ''}
    `;

    document.querySelector('.article-body').innerHTML = brief.stories.map(s => renderStoryHTML(s)).join('');
    document.title = brief.title + ' — The Geopol Brief';
}

// Route based on page
if (document.querySelector('.article-header')) {
    renderBriefPage();
} else {
    renderHomePage();
}