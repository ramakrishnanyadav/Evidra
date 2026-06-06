
    const state = {
        candidates: [],
        selectedCandidateId: null,
        isBlindMode: false,
        currentPersona: 'startup_generalist',
        searchQuery: '',
        currentView: 'pipeline',
        token: localStorage.getItem('evidra_token') || null,
        organizationId: localStorage.getItem('evidra_org_id') || null
    }

    function getAuthHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${state.token}`
        }
    }

    function showAuthModal() {
        document.getElementById('auth-modal').classList.remove('hidden')
    }

    function hideAuthModal() {
        document.getElementById('auth-modal').classList.add('hidden')
    }

    function showRegister() {
        document.getElementById('login-form').classList.add('hidden')
        document.getElementById('register-form').classList.remove('hidden')
        document.getElementById('auth-error').classList.add('hidden')
    }

    function showLogin() {
        document.getElementById('register-form').classList.add('hidden')
        document.getElementById('login-form').classList.remove('hidden')
        document.getElementById('auth-error').classList.add('hidden')
    }

    function showAuthError(message) {
        const el = document.getElementById('auth-error')
        el.textContent = message
        el.classList.remove('hidden')
    }

    async function handleLogin() {
        const email = document.getElementById('login-email').value
        const password = document.getElementById('login-password').value

        if (!email || !password) {
            showAuthError('Email and password required')
            return
        }

        const formData = new FormData()
        formData.append('username', email)
        formData.append('password', password)

        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                body: formData
            })

            if (!response.ok) {
                const error = await response.json()
                showAuthError(error.detail || 'Login failed')
                return
            }

            const data = await response.json()
            state.token = data.access_token
            state.organizationId = data.organization_id
            localStorage.setItem('evidra_token', data.access_token)
            localStorage.setItem('evidra_org_id', data.organization_id)
            hideAuthModal()
            await loadCandidates()

        } catch (err) {
            showAuthError('Connection error. Check server status.')
        }
    }

    async function handleRegister() {
        const org = document.getElementById('reg-org').value
        const email = document.getElementById('reg-email').value
        const password = document.getElementById('reg-password').value

        if (!org || !email || !password) {
            showAuthError('All fields required')
            return
        }

        if (password.length < 8) {
            showAuthError('Password must be at least 8 characters')
            return
        }

        try {
            const response = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    organization_name: org,
                    email: email,
                    password: password
                })
            })

            if (!response.ok) {
                const error = await response.json()
                showAuthError(error.detail || 'Registration failed')
                return
            }

            const data = await response.json()
            state.token = data.access_token
            state.organizationId = data.organization_id
            localStorage.setItem('evidra_token', data.access_token)
            localStorage.setItem('evidra_org_id', data.organization_id)
            hideAuthModal()
            await loadCandidates()

        } catch (err) {
            showAuthError('Connection error. Check server status.')
        }
    }

    function handleUnauthorized() {
        state.token = null
        state.organizationId = null
        localStorage.removeItem('evidra_token')
        localStorage.removeItem('evidra_org_id')
        showAuthModal()
    }

    async function authenticatedFetch(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            headers: {
                ...getAuthHeaders(),
                ...(options.headers || {})
            }
        })

        if (response.status === 401) {
            handleUnauthorized()
            return null
        }

        return response
    }


    function setState(updates) {
        Object.assign(state, updates)
        render()
    }

    async function loadCandidates() {
        const response = await authenticatedFetch(`/api/v1/candidates?persona=${state.currentPersona}&limit=100`);
        if (!response) return;
        const data = await response.json();
        const candidatesArray = data.data || data.items || data;
        setState({ candidates: Array.isArray(candidatesArray) ? candidatesArray : [] });
        if (state.candidates.length > 0 && !state.selectedCandidateId) {
            selectCandidate(state.candidates[0].id);
        }
    }

    async function rerankCandidates(persona) {
        const response = await authenticatedFetch(
            `/api/v1/candidates/jobs/demo-job-01/rerank?persona=${persona}`,
            { method: 'POST' }
        );
        if (!response) return;
        const data = await response.json();
        setState({
            candidates: data.data.map(item => ({
                ...item.profile,
                score: item.score
            })),
            currentPersona: persona
        });
    }

    function selectCandidate(id) {
        setState({ selectedCandidateId: id });
        const candidate = state.candidates.find(c => c.id === id);
        if (candidate) {
            renderReasoningTimeline(candidate);
            renderExplainability(candidate);
            
            // Update Evidence Analysis
            const evidenceSource = document.getElementById('evidence-source');
            const evidenceJson = document.getElementById('evidence-json');
            if (evidenceSource) evidenceSource.textContent = candidate.resume_text || "No raw resume text available.";
            if (evidenceJson) {
                const strengthsHTML = (candidate.hidden_strengths || []).map(hs => `<span class="inline-block bg-tertiary/10 text-tertiary px-3 py-1 rounded-full text-xs font-medium mr-2 mb-2 border border-tertiary/20">${hs.domain}</span>`).join('');
                
                evidenceJson.innerHTML = `
                    <div class="mb-6">
                        <h3 class="text-xs uppercase tracking-wider text-on-surface-variant mb-2">Candidate Details</h3>
                        <div class="text-xl font-medium text-on-surface">${candidate.name || 'Anonymous Candidate'}</div>
                        <div class="text-sm text-primary mt-1">${candidate.title || ''}</div>
                    </div>
                    
                    <div class="mb-6">
                        <h3 class="text-xs uppercase tracking-wider text-on-surface-variant mb-3">Top Detected Strengths</h3>
                        <div>${strengthsHTML || '<span class="text-on-surface-variant/50 italic">No strengths detected.</span>'}</div>
                    </div>
                    
                    <div class="mb-6">
                        <h3 class="text-xs uppercase tracking-wider text-on-surface-variant mb-2">AI Summary</h3>
                        <p class="text-on-surface/90 leading-relaxed">${candidate.reasoning?.narrative || 'Summary pending...'}</p>
                        
                        <div class="mt-4 pt-4 border-t border-outline-variant/30">
                            <h4 class="text-[10px] uppercase tracking-wider text-on-surface-variant mb-2">Evidence Sources</h4>
                            <div class="grid grid-cols-2 gap-2 text-[11px] text-on-surface-variant/80">
                                <div class="flex items-center gap-1.5"><span class="text-tertiary">✓</span> Resume Parsing</div>
                                <div class="flex items-center gap-1.5"><span class="text-tertiary">✓</span> Repository Activity</div>
                                <div class="flex items-center gap-1.5"><span class="text-tertiary">✓</span> Technical Skill Correlation</div>
                                <div class="flex items-center gap-1.5"><span class="text-tertiary">✓</span> Inference Engine</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-6 bg-surface-secondary/50 border border-outline-variant rounded-lg p-4">
                        ${(!candidate.score || candidate.score > 0.5) ? `
                            <h3 class="text-xs uppercase tracking-wider text-on-surface-variant mb-3 flex items-center gap-2">
                                <span class="material-symbols-outlined text-[16px] text-tertiary">assignment_turned_in</span> Hiring Recommendation
                            </h3>
                            <div class="text-[12px] text-on-surface-variant mb-2">Strong fit for:</div>
                            <ul class="list-disc pl-5 space-y-1 text-[13px] text-on-surface/90">
                                <li>IoT Engineer</li>
                                <li>Embedded Systems Developer</li>
                                <li>Technical Product Engineer</li>
                            </ul>
                        ` : `
                            <h3 class="text-xs uppercase tracking-wider text-secondary mb-3 flex items-center gap-2">
                                <span class="material-symbols-outlined text-[16px]">warning</span> Concerns
                            </h3>
                            <ul class="list-disc pl-5 space-y-1 text-[13px] text-on-surface/90">
                                <li>Limited project depth</li>
                                <li>No verifiable repository evidence</li>
                                <li>Skills claimed but not demonstrated</li>
                            </ul>
                        `}
                    </div>

                    <div class="mb-6">
                        <h3 class="text-xs uppercase tracking-wider text-on-surface-variant mb-2">Technical Capabilities</h3>
                        <ul class="list-disc pl-5 space-y-1 text-on-surface/80">
                            ${(candidate.extracted_skills || []).slice(0,3).map(s => s.skill_name || s).map(cap => `<li>${cap}</li>`).join('') || '<li>No capabilities extracted.</li>'}
                        </ul>
                    </div>
                    ${renderEducationExperience(candidate)}
                `;
            }
        }
    }

    function renderEducationExperience(candidate) {
        const edu = candidate.education || []
        const exp = candidate.work_experience || []
        
        if (!edu.length && !exp.length) return ''
        
        return `
        <div class="intel-module mb-6" id="experience-vector">
            <h3 class="text-xs uppercase tracking-wider text-on-surface-variant mb-2">EXPERIENCE VECTOR</h3>
            <div class="space-y-3">
            ${exp.map(role => `
                <div class="experience-item bg-surface-secondary/50 p-2 rounded border border-outline-variant">
                    <div class="flex justify-between items-start">
                        <span class="font-medium text-sm text-on-surface">${role.title || 'Unknown Role'}</span>
                        <span class="text-xs font-mono text-tertiary">
                            ${role.duration_months ? Math.round(role.duration_months / 12 * 10) / 10 + ' YRS' : ''}
                            ${role.is_current ? '<span class="ml-1 bg-tertiary/20 text-tertiary px-1 rounded">CURRENT</span>' : ''}
                        </span>
                    </div>
                    <div class="text-xs text-on-surface-variant mt-1">${role.company || ''}</div>
                </div>
            `).join('')}
            </div>
        </div>
        <div class="intel-module mb-6" id="education-vector">
            <h3 class="text-xs uppercase tracking-wider text-on-surface-variant mb-2">EDUCATION SIGNAL</h3>
            <div class="space-y-2">
            ${edu.map(e => `
                <div class="education-item bg-surface-secondary/50 p-2 rounded border border-outline-variant">
                    <div class="font-medium text-sm text-on-surface">${e.degree || ''} ${e.field_of_study || ''}</div>
                    <div class="flex justify-between items-center text-xs text-on-surface-variant mt-1">
                        <span class="institution">${e.institution || ''}</span>
                        <span class="grad-year font-mono">${e.graduation_year || ''}</span>
                    </div>
                </div>
            `).join('')}
            </div>
        </div>
        `
    }

    function renderHiddenStrength(candidate) {
        if (!candidate.hidden_strengths?.length) return '';
        const hs = candidate.hidden_strengths[0];
        const repos = hs.evidence_repos || [];
        return `
            <div class="border-2 border-secondary bg-secondary/10 p-padding-md rounded-sm reasoning-transition group relative shadow-[0_0_30px_rgba(238,193,66,0.15)] mt-6" id="hidden-strength-card">
                <div class="absolute -top-3 left-4 bg-secondary text-[#06070A] font-mono text-[9px] uppercase tracking-widest px-3 py-1 rounded-sm shadow-[0_0_15px_rgba(238,193,66,0.5)] flex items-center gap-1.5 font-bold">
                    <span class="material-symbols-outlined text-[12px]">search_insights</span> DISCOVERY EVENT
                </div>
                <div class="flex items-center justify-between mb-3 mt-2">
                    <div class="flex items-center gap-2">
                        <span class="font-mono text-[11px] text-secondary uppercase tracking-widest font-bold">Previously Undetected Capability Found: <br><span class="text-[14px]">${hs.domain}</span></span>
                    </div>
                    <span class="font-mono text-[9px] text-secondary px-2 py-0.5 border border-secondary/30 bg-secondary/10 rounded-full uppercase tracking-tighter">HIGH CONFIDENCE</span>
                </div>
                <p class="text-[13px] text-on-surface/90 leading-relaxed font-normal mb-3">
                    ${hs.description}
                </p>
                <div class="flex gap-2 flex-wrap">
                    ${repos.map(r => 
                        `<a href="https://github.com/${candidate.github_username}/${r}" target="_blank" class="px-2 py-0.5 bg-surface-secondary border border-outline-variant text-[9px] font-mono text-on-surface-variant hover:text-on-surface hover:border-on-surface-variant transition-colors uppercase rounded-sm">${r}</a>`
                    ).join('')}
                </div>
            </div>
        `;
    }

    async function renderReasoningTimeline(candidate) {
        // Hidden Strengths
        document.getElementById('dynamic-hidden-strength').innerHTML = renderHiddenStrength(candidate);
        
        // Narrative
        const narrativeDiv = document.getElementById('narrative-container');
        if (candidate.reasoning?.narrative) {
            narrativeDiv.innerHTML = `<span class="font-mono text-[10px] text-primary uppercase block mb-2 tracking-wider">Intelligence Analyst Narrative</span>${candidate.reasoning.narrative}`;
        } else {
            narrativeDiv.innerHTML = 'Intelligence narrative is pending...';
        }

        // Timeline
        const container = document.getElementById('reasoning-timeline');
        container.innerHTML = '<div class="text-xs text-on-surface-variant animate-pulse">Fetching inference timeline...</div>';
        
        const response = await authenticatedFetch(`/api/v1/candidates/${candidate.id}/timeline`);
        if (!response) return;
        const data = await response.json();
        const timelineEvents = data.timeline || [];
        
        container.innerHTML = '<div class="absolute left-[7px] top-2 bottom-2 w-px bg-outline-variant"></div>';
        
        timelineEvents.forEach((event, i) => {
            setTimeout(() => {
                const isHiddenStrength = event.action === 'Hidden Strength Found' || event.action.includes('Hidden Capability');
                const glow = isHiddenStrength ? 'shadow-[0_0_8px_#eec142] bg-secondary border-surface' : 'bg-tertiary border-surface shadow-[0_0_8px_#42e18d]';
                const textCls = isHiddenStrength ? 'text-secondary' : 'text-tertiary';
                
                const el = document.createElement('div');
                el.className = 'relative transition-all duration-300 p-2 -m-2 rounded-sm';
                el.innerHTML = `
                    <div class="absolute -left-[23px] top-3 w-2 h-2 ${glow} rounded-full border"></div>
                    <div class="text-[11px] font-medium uppercase tracking-wider ${textCls}">${event.action}</div>
                    <div class="text-[9px] font-mono text-on-surface-variant/60 mt-1 lowercase">${event.details || ''}</div>
                `;
                el.style.opacity = '0';
                el.style.transform = 'translateY(4px)';
                container.appendChild(el);
                
                requestAnimationFrame(() => {
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                    setTimeout(() => {
                        // Stabilize color if not gold
                        if (!isHiddenStrength) {
                            el.querySelector('div:nth-child(2)').classList.replace('text-tertiary', 'text-on-surface');
                            el.querySelector('div:nth-child(1)').classList.remove('shadow-[0_0_8px_#42e18d]');
                        }
                    }, 400);
                });
            }, 500 + (i * 300));
        });

        setTimeout(() => {
            const stabilized = document.createElement('div');
            stabilized.className = 'pt-2 relative overflow-hidden transition-all duration-300';
            stabilized.innerHTML = `
                <div class="flex items-center gap-3 font-mono text-[10px] text-tertiary uppercase tracking-[0.2em]">
                    <div class="relative w-2 h-2">
                        <span class="absolute inset-0 bg-tertiary rounded-full"></span>
                        <span class="absolute inset-0 bg-tertiary rounded-full animate-ping"></span>
                    </div>
                    SIGNAL STABILIZED
                </div>
            `;
            container.appendChild(stabilized);
        }, 500 + (timelineEvents.length * 300) + 200);
    }

    async function renderExplainability(candidate) {
        const container = document.getElementById('dynamic-explainability');
        container.innerHTML = '<div class="text-xs text-on-surface-variant animate-pulse">Computing explainability...</div>';
        
        try {
            const response = await authenticatedFetch(`/api/v1/candidates/${candidate.id}/explain?persona=${state.currentPersona}`);
            if (!response) return;
            const data = await response.json();
            
            const breakdown = data.breakdown || {};
            let html = '<div class="font-mono text-[9px] text-on-surface-variant/40 uppercase tracking-[0.15em] mb-2">Score Determinants</div>';
            
            const formatImpact = (impact) => {
                const color = impact === 'critical' ? 'text-secondary bg-secondary/10 border-secondary/30' :
                              impact === 'high' ? 'text-tertiary bg-tertiary/10 border-tertiary/30' :
                              'text-indigo-signal bg-indigo-signal/10 border-indigo-signal/30';
                return `<span class="font-mono text-[9px] ${color} px-2 py-0.5 border rounded-sm uppercase tracking-tighter">${impact} IMPACT</span>`;
            };

            if (breakdown.verified_skills) {
                html += `<div class="flex items-center justify-between py-2 border-b border-outline-variant/50">
                    <span class="text-xs font-medium text-on-surface">Verified Skills</span>
                    ${formatImpact(breakdown.verified_skills.impact)}
                </div>`;
            }
            if (breakdown.hidden_strength_bonus) {
                html += `<div class="flex items-center justify-between py-2 border-b border-outline-variant/50">
                    <span class="text-xs font-medium text-on-surface">Hidden Strength</span>
                    ${formatImpact(breakdown.hidden_strength_bonus.impact)}
                </div>`;
            }
            if (breakdown.role_fit) {
                html += `<div class="flex items-center justify-between py-2 border-b border-outline-variant/50">
                    <span class="text-xs font-medium text-on-surface">Role Fit</span>
                    ${formatImpact(breakdown.role_fit.impact)}
                </div>`;
            }
            
            container.innerHTML = html;
        } catch (e) {
            container.innerHTML = '<div class="text-xs text-red-400">Explainability computation failed.</div>';
        }
    }

    async function executeCommand(query) {
        let responsePanel = document.getElementById('command-response');
        responsePanel.textContent = 'Executing semantic candidate search...';
        responsePanel.style.display = 'block';
        
        try {
            const response = await authenticatedFetch('/api/v1/candidates/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    job_id: null
                })
            });
            
            if (!response || !response.ok) {
                responsePanel.textContent = 'Command execution failed.';
                return;
            }
            
            const data = await response.json();
            
            setState({
                candidates: data.data || [],
                searchQuery: '' // Clear standard search filter
            });
            
            if (data.data && data.data.length > 0) {
                selectCandidate(data.data[0].id);
                responsePanel.textContent = `Found ${data.data.length} matches for: "${query}"`;
            } else {
                responsePanel.textContent = 'No candidates match this semantic profile.';
            }
            
            setTimeout(() => {
                responsePanel.style.display = 'none';
            }, 5000);
            
        } catch (e) {
            responsePanel.textContent = 'Command execution error.';
        }
    }

    function render() {
        // 1. Render Nav
        document.querySelectorAll('.nav-tab').forEach(tab => {
            if (tab.dataset.persona === state.currentPersona) {
                tab.className = 'nav-tab text-primary border-b border-primary pb-0.5 text-xs font-medium uppercase tracking-wider cursor-pointer';
            } else {
                tab.className = 'nav-tab text-on-surface-variant hover:text-on-surface text-xs font-medium uppercase tracking-wider cursor-pointer';
            }
        });

        // Render Left Rail View Nav
        document.querySelectorAll('.nav-item').forEach(item => {
            if (item.dataset.view === state.currentView) {
                item.className = 'nav-item flex items-center gap-3 px-padding-md py-2 bg-primary/5 text-primary border-r-2 border-primary cursor-pointer transition-colors';
            } else {
                item.className = 'nav-item flex items-center gap-3 px-padding-md py-2 text-on-surface-variant hover:bg-surface-secondary transition-colors cursor-pointer';
            }
        });

        const views = ['pipeline', 'overview', 'competency', 'evidence'];
        views.forEach(v => {
            const el = document.getElementById(`view-${v}`);
            if (el) {
                if (state.currentView === v) el.classList.remove('hidden');
                else el.classList.add('hidden');
            }
        });

        // 1.1 Render Overview Dynamic Metrics
        const elTotal = document.getElementById('overview-total');
        const elHigh = document.getElementById('overview-high');
        const elHealth = document.getElementById('health-candidates');
        
        if (elTotal) elTotal.textContent = state.candidates.length.toLocaleString();
        if (elHigh) elHigh.textContent = state.candidates.filter(c => (c.score || 0) > 0.8).length.toLocaleString();
        if (elHealth) elHealth.textContent = state.candidates.length;
        
        if (state.candidates.length > 0) {
            // Generate Telemetry
            const telemetryList = document.getElementById('overview-telemetry');
            if (telemetryList) {
                telemetryList.innerHTML = state.candidates.slice(0, 50).map((c, i) => {
                    const timeStr = i === 0 ? "Just now" : `${i * 2} mins ago`;
                    const domain = c.hidden_strengths?.[0]?.domain || 'Generalist';
                    const name = c.name || 'A candidate';
                    return `<div class="flex items-start gap-4 p-3 hover:bg-surface-secondary/50 rounded-lg transition-colors border border-transparent hover:border-outline-variant/50">
                        <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary flex-shrink-0">
                            <span class="material-symbols-outlined text-[20px]">person_check</span>
                        </div>
                        <div>
                            <div class="text-on-surface font-medium">${name}'s resume was analyzed</div>
                            <div class="text-on-surface-variant text-xs mt-1">Our AI identified them as a strong match for <span class="text-tertiary font-medium">${domain}</span>.</div>
                            <div class="text-xs text-on-surface-variant/50 mt-2">${timeStr}</div>
                        </div>
                    </div>`;
                }).join('');
            }
            
            // Build Competency Graph
            const graphContainer = document.getElementById('competency-canvas');
            const subtitle = document.getElementById('competency-subtitle');
            
            if (graphContainer && state.selectedCandidateId) {
                const candidate = state.candidates.find(c => c.id === state.selectedCandidateId);
                if (candidate) {
                    const nodes = [];
                    // Add extracted skills
                    (candidate.extracted_skills || []).forEach(skill => {
                        let rawName = skill.skill_name || skill;
                        if (rawName.includes('Microsoft Office')) rawName = 'Documentation';
                        if (rawName.includes('Database')) rawName = 'Database';
                        if (rawName.includes('Frontend')) rawName = 'Frontend';
                        if (rawName.includes('IoT')) rawName = 'IoT Systems';
                        if (rawName.includes('Artificial Intelligence')) rawName = 'AI/ML';
                        
                        // Clean up strings, take first part if comma separated, truncate
                        let cleanName = rawName.split(',')[0].trim();
                        if (cleanName.length > 18) cleanName = cleanName.substring(0, 15) + '...';

                        nodes.push({
                            name: cleanName,
                            type: skill.verified ? 'verified' : 'claimed',
                            color: skill.verified ? '#6c88ff' : '#ffffff'
                        });
                    });
                    
                    // Add hidden strengths
                    (candidate.hidden_strengths || []).forEach(hs => {
                        nodes.push({
                            name: hs.domain,
                            type: 'discovered',
                            color: '#eec142' // Gold
                        });
                    });
                    
                    if (subtitle) subtitle.textContent = `Visualizing ${nodes.length} verified & discovered capabilities`;
                    
                    if (nodes.length > 0) {
                        let svgInner = '';
                        const centerX = 50;
                        const centerY = 50;
                        const radius = 32;
                        
                        nodes.forEach((node, i) => {
                            const angle = (i / nodes.length) * 2 * Math.PI - Math.PI / 2;
                            const x = centerX + radius * Math.cos(angle);
                            const y = centerY + radius * Math.sin(angle);
                            const size = node.type === 'discovered' ? 4 : 2;
                            const pulseCls = node.type === 'discovered' ? 'node-pulse' : '';
                            
                            // Line to center
                            svgInner += `<line x1="${centerX}" y1="${centerY}" x2="${x}" y2="${y}" stroke="${node.color}" stroke-opacity="0.3" stroke-width="0.5"></line>`;
                            
                            // Node circle
                            svgInner += `<circle cx="${x}" cy="${y}" r="${size}" fill="${node.color}" class="${pulseCls}"></circle>`;
                            
                            // Label
                            svgInner += `<text x="${x}" y="${y + size + 6}" fill="rgba(255,255,255,0.8)" font-family="sans-serif" font-size="2.5" text-anchor="middle">${node.name.substring(0, 25)}</text>`;
                        });
                        
                        // Center Candidate Node
                        svgInner += `<circle cx="${centerX}" cy="${centerY}" r="5" fill="#0E1016" stroke="#6c88ff" stroke-width="1"></circle>`;
                        svgInner += `<text x="${centerX}" y="${centerY + 1}" fill="#6c88ff" font-family="sans-serif" font-size="2.5" text-anchor="middle" font-weight="bold">CANDIDATE</text>`;
                        svgInner += `<circle cx="${centerX}" cy="${centerY}" r="7" fill="none" stroke="#6c88ff" stroke-width="0.5" stroke-opacity="0.3"><animate attributeName="r" values="7;11;7" dur="3s" repeatCount="indefinite"></animate></circle>`;
                        
                        graphContainer.innerHTML = `<svg class="w-full h-full" viewBox="0 0 100 100">${svgInner}</svg>`;
                    } else {
                        graphContainer.innerHTML = '<div class="text-on-surface-variant text-sm font-mono absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">No capability data available for mapping.</div>';
                    }
                }
            } else {
            const telemetryList = document.getElementById('overview-telemetry');
            if (telemetryList) {
                telemetryList.innerHTML = `
                    <div class="flex flex-col items-center justify-center h-32 text-center opacity-50 mt-4">
                        <span class="material-symbols-outlined text-[24px] mb-2 text-outline-variant">analytics</span>
                        <div class="text-on-surface-variant text-xs font-mono">No intelligence events recorded.<br>Awaiting candidate ingestion.</div>
                    </div>`;
            }
            const graphContainer = document.getElementById('competency-canvas');
            if (graphContainer) {
                graphContainer.innerHTML = `
                    <div class="flex flex-col items-center justify-center absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-50">
                        <span class="material-symbols-outlined text-[32px] text-outline-variant mb-2">hub</span>
                        <div class="text-on-surface-variant text-xs font-mono text-center">Awaiting target selection<br>to generate competency network.</div>
                    </div>`;
            }
            }
        }
        
        // 2. Render Blind Review Toggle
        const blindToggleInner = state.isBlindMode 
            ? '<div class="absolute left-0.5 top-0.5 w-2 h-2 bg-on-secondary rounded-full"></div>' 
            : '<div class="absolute right-0.5 top-0.5 w-2 h-2 bg-on-surface rounded-full"></div>';
        const blindToggleBg = state.isBlindMode ? 'bg-secondary' : 'bg-surface-secondary';
        
        document.getElementById('btn-blind-review').innerHTML = `
            <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-[16px]">${state.isBlindMode ? 'visibility_off' : 'visibility'}</span>
                <span class="font-mono text-[10px] uppercase">Blind Review</span>
            </div>
            <div class="w-6 h-3 ${blindToggleBg} rounded-full relative transition-all">
                ${blindToggleInner}
            </div>
        `;

        // 3. Render Chamber Header
        const header = document.getElementById('chamber-header');
        if (state.selectedCandidateId) {
            const index = state.candidates.findIndex(c => c.id === state.selectedCandidateId);
            const c = state.candidates[index];
            if (c) {
                header.textContent = state.isBlindMode ? `Candidate ${index + 1}` : (c.name || 'Reasoning Chamber');
            }
        } else {
            header.textContent = 'Reasoning Chamber';
        }

        // 3. Render Candidates
        const list = document.getElementById('candidate-list');
        const query = state.searchQuery.toLowerCase();
        const filteredCandidates = state.candidates.filter(c => 
            !query || 
            (c.name && c.name.toLowerCase().includes(query)) || 
            (c.id && c.id.toLowerCase().includes(query))
        );

        // Update Pipeline Subtitle
        const pipelineSubtitle = document.getElementById('pipeline-subtitle');
        if (pipelineSubtitle) {
            pipelineSubtitle.textContent = `Displaying ${filteredCandidates.length} matches // Query: '${state.searchQuery || 'ALL'}'`;
        }

        if (filteredCandidates.length === 0) {
            list.innerHTML = `
                <div class="flex flex-col items-center justify-center h-48 text-center border border-dashed border-outline-variant/40 rounded-2xl bg-surface/30 mt-8">
                    <span class="material-symbols-outlined text-outline-variant text-[40px] mb-3 opacity-50">person_add</span>
                    <div class="text-on-surface text-sm font-medium mb-1">Intelligence Database Empty</div>
                    <div class="text-on-surface-variant text-xs font-mono opacity-70">Click "Add Participant" in the top right<br>to upload a candidate resume.</div>
                </div>`;
            return;
        }

        list.innerHTML = filteredCandidates.map((c, index) => {
            const isSelected = c.id === state.selectedCandidateId;
            const borderCls = isSelected ? 'border-indigo-signal/60 shadow-[0_0_30px_rgba(108,136,255,0.15)] bg-surface/90' : 'border-outline-variant/30 hover:border-outline-variant/60 hover:bg-surface-secondary/40 cursor-pointer';
            
            // Name masking
            const displayName = state.isBlindMode ? `Candidate ${index + 1}` : (c.name || `Candidate ${c.id.substring(0,8)}`);
            
            // Blind mode visual indicator (amber)
            const headerAlert = state.isBlindMode && isSelected 
                ? `<div class="bg-secondary/20 text-secondary text-[9px] font-mono uppercase px-2 py-1 border-b border-secondary/30 w-full text-center tracking-widest rounded-t-xl absolute top-0 left-0 right-0">Name Redacted for Objective Evaluation</div>`
                : '';

            return `
                <div class="tile-transition border rounded-xl p-5 relative group ${borderCls} backdrop-blur-xl transition-all duration-300" onclick="selectCandidate('${c.id}')">
                    ${headerAlert}
                    <div class="flex justify-between items-start ${state.isBlindMode && isSelected ? 'mt-4' : 'mt-1'}">
                        <div class="flex items-center gap-4">
                            <div class="w-11 h-11 bg-surface border ${isSelected ? 'border-indigo-signal/50 shadow-[0_0_15px_rgba(108,136,255,0.2)]' : 'border-outline-variant/50'} rounded-lg flex items-center justify-center transition-all">
                                <span class="material-symbols-outlined text-[${isSelected?'24px':'20px'}] ${isSelected ? 'text-indigo-signal' : 'text-on-surface-variant'}">${isSelected?'fingerprint':'person'}</span>
                            </div>
                            <div>
                                <div class="text-[15px] font-medium flex items-center gap-2 text-white">
                                    ${displayName}
                                    ${isSelected ? '<span class="w-2 h-2 bg-secondary rounded-full shadow-[0_0_8px_rgba(238,193,66,0.6)] animate-pulse"></span>' : ''}
                                </div>
                                <div class="font-mono text-[10px] text-on-surface-variant opacity-60">ID: ${c.id.substring(0,12).toUpperCase()}</div>
                            </div>
                        </div>
                        <div class="flex flex-col items-end gap-1.5">
                            ${isSelected ? '<div class="font-mono text-[9px] text-on-surface-variant/40 uppercase mb-1">Status</div>' : ''}
                            <div class="font-mono text-[9px] ${c.processing_status === 'failed' ? 'text-red-400 border-red-500/30 bg-red-500/10' : (c.processing_status === 'completed' ? 'text-tertiary border-tertiary/30 bg-tertiary/10' : 'text-secondary border-secondary/30 bg-secondary/10')} px-2.5 py-0.5 border rounded-full uppercase tracking-tighter">
                                ${c.processing_status || 'processing'}
                            </div>
                            <div class="font-mono text-[9px] ${isSelected?'text-tertiary border-tertiary/30 bg-tertiary/5':'text-indigo-signal border-indigo-signal/30 bg-indigo-signal/5'} px-2.5 py-0.5 border rounded-full uppercase tracking-tighter mt-1">
                                ${c.reasoning?.recommendation === 'shortlist' ? 'HIGH CONFIDENCE' : (c.reasoning?.recommendation === 'review' ? 'MEDIUM CONFIDENCE' : 'LOW CONFIDENCE')}
                            </div>
                        </div>
                    </div>
                    
                    ${isSelected ? `
                    <div class="flex flex-wrap gap-1.5 mt-4">
                        <span class="px-2 py-0.5 bg-surface-secondary/40 border border-outline-variant text-[8px] font-mono text-on-surface-variant/60 uppercase">VERIFIED_SOURCE</span>
                        ${c.github_username ? '<span class="px-2 py-0.5 bg-surface-secondary/40 border border-outline-variant text-[8px] font-mono text-on-surface-variant/60 uppercase">OSS_ACTIVITY</span>' : ''}
                        <span class="px-2 py-0.5 bg-indigo-signal/5 border border-indigo-signal/20 text-[8px] font-mono text-indigo-signal/60 uppercase">SIGNAL_MATCH</span>
                        <span class="px-2 py-0.5 text-[8px] font-mono text-on-surface-variant/30">+${(c.extracted_skills?.length || 0)}</span>
                    </div>
                    <!-- Simplified Architecture Grid for dynamic rendering -->
                    <div class="mt-6 grid grid-cols-4 gap-4">
                        <div class="space-y-2 pb-2 border-b border-outline-variant/30">
                            <div class="font-mono text-[8px] text-on-surface-variant/30 uppercase tracking-wider">SIGNAL MATCH</div>
                            <div class="text-xs ${c.score > 0 ? (c.score > 0.8 ? 'text-tertiary' : 'text-secondary') : 'text-indigo-signal opacity-70'} font-mono">${c.score > 0 ? (c.score > 0.8 ? 'HIGH MATCH' : 'SIGNAL STRONG') : 'ANALYZING'}</div>
                        </div>
                        <div class="space-y-2 pb-2 border-b border-outline-variant/30">
                            <div class="font-mono text-[8px] text-on-surface-variant/30 uppercase tracking-wider">SKILLS</div>
                            <div class="text-xs text-primary font-mono">${c.extracted_skills?.length || 0}</div>
                        </div>
                        <div class="space-y-2 pb-2 border-b border-outline-variant/30">
                            <div class="font-mono text-[8px] text-on-surface-variant/30 uppercase tracking-wider">REPOS</div>
                            <div class="text-xs text-primary font-mono">${c.github_signals?.repos?.length || 0}</div>
                        </div>
                    </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    window.addEventListener('load', async () => {
        if (!state.token) {
            showAuthModal()
        } else {
            hideAuthModal()
            await loadCandidates()
        }
    })

    document.addEventListener('DOMContentLoaded', () => {
        // Init Event Listeners
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const persona = e.target.dataset.persona;
                rerankCandidates(persona);
            });
        });

        document.getElementById('btn-blind-review').addEventListener('click', () => {
            setState({ isBlindMode: !state.isBlindMode });
        });

        document.getElementById('cmd-btn').addEventListener('click', () => {
            const query = document.getElementById('cmd-input').value;
            if (query) executeCommand(query);
        });

        document.getElementById('cmd-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = e.target.value;
                if (query) executeCommand(query);
            }
        });

        // Live Signal Feed Update (Simulated background task monitoring)
        const feed = document.getElementById('signal-feed');
        const logs = [
            "[<span class='text-tertiary/60'>VERIFY</span>] Commits cross-referenced",
            "[<span class='text-indigo-signal/60'>SIGNAL</span>] Pattern 0x92 match confirmed",
            "[<span class='text-secondary/60'>DISCOVERY</span>] Lead-equivalent signal",
            "[<span class='text-tertiary/60'>VERIFY</span>] Nodes stable"
        ];
        let logIndex = 0;
        setInterval(() => {
            const div = document.createElement('div');
            div.innerHTML = logs[logIndex % logs.length];
            div.className = 'opacity-0 transition-opacity duration-300';
            feed.insertBefore(div, feed.lastElementChild);
            setTimeout(() => div.classList.replace('opacity-0', 'opacity-100'), 50);
            if (feed.children.length > 7) feed.removeChild(feed.firstChild);
            logIndex++;
        }, 6000);
        
        // Background graph animation
        const nodes = ['distributed', 'memory', 'oss', 'backend', 'concurrency', 'api'];
        setInterval(() => {
            const randomNode = nodes[Math.floor(Math.random() * nodes.length)];
            const trace = document.getElementById(`trace-${randomNode}`);
            const nodeElem = document.getElementById(`node-${randomNode}`);
            if (trace && nodeElem) {
                trace.classList.remove('signal-active');
                void trace.offsetWidth; 
                trace.classList.add('signal-active');
                nodeElem.classList.add('highlight-node');
                setTimeout(() => nodeElem.classList.remove('highlight-node'), 1500);
            }
        }, 5000);

        // Search Input Logic
        document.getElementById('search-input').addEventListener('input', (e) => {
            setState({ searchQuery: e.target.value });
        });

        // Upload Resume Logic
        document.getElementById('upload-resume').addEventListener('change', async (e) => {
            if (!e.target.files.length) return;
            const file = e.target.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            const btnText = document.getElementById('upload-text');
            const originalText = btnText.textContent;
            btnText.textContent = 'Uploading...';
            
            try {
                const response = await authenticatedFetch('/api/v1/candidates/upload', {
                    method: 'POST',
                    body: formData
                });
                if (response.ok) {
                    await loadCandidates();
                } else {
                    let msg = 'Unknown error';
                    const text = await response.text();
                    try {
                        const err = JSON.parse(text);
                        if (err.detail) {
                            if (typeof err.detail === 'string') msg = err.detail;
                            else if (err.detail.message) msg = err.detail.message;
                            else if (Array.isArray(err.detail)) msg = err.detail[0]?.msg || 'Validation error';
                        } else if (err.message) {
                            msg = err.message;
                        }
                    } catch (e) {
                        msg = text || response.statusText;
                    }
                    alert('Upload failed: ' + msg);
                }
            } catch (err) {
                console.error(err);
                alert('Upload error: Network issue or server unreachable.');
            } finally {
                btnText.textContent = originalText;
                e.target.value = ''; // Reset input
            }
        });

        // Navigation Tabs Logic
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                setState({ currentView: item.dataset.view });
            });
        });

        // Load data on boot
        loadCandidates();
    });
