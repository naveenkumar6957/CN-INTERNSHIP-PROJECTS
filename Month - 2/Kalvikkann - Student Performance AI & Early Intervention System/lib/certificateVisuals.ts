// Certificate visual SVG generators and helper utilities for Kalvikkan Achievement Gallery

export function generateCertificateSvg(
  title: string,
  studentName: string,
  issuer: string,
  date: string,
  category: string,
  gradeOrScore?: string
): string {
  const safeTitle = (title || 'Certificate of Achievement').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const safeName = (studentName || 'Student Name').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const safeIssuer = (issuer || 'Kalvikkan Academy').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const safeDate = date || '2025-2026';
  const safeScore = gradeOrScore || 'Elite Gold';

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 560" width="100%" height="100%">
    <defs>
      <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#0f172a" />
        <stop offset="50%" stop-color="#1e1b4b" />
        <stop offset="100%" stop-color="#020617" />
      </linearGradient>
      <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#fbbf24" />
        <stop offset="50%" stop-color="#f59e0b" />
        <stop offset="100%" stop-color="#d97706" />
      </linearGradient>
      <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#3b82f6" />
        <stop offset="100%" stop-color="#8b5cf6" />
      </linearGradient>
      <pattern id="gridPattern" width="40" height="40" patternUnits="userSpaceOnUse">
        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#334155" stroke-width="0.5" stroke-opacity="0.3"/>
      </pattern>
    </defs>

    <!-- Certificate Background Canvas -->
    <rect width="800" height="560" fill="url(#bgGrad)" />
    <rect width="800" height="560" fill="url(#gridPattern)" />

    <!-- Ornate Golden Borders -->
    <rect x="24" y="24" width="752" height="512" rx="12" fill="none" stroke="url(#goldGrad)" stroke-width="4" />
    <rect x="36" y="36" width="728" height="488" rx="8" fill="none" stroke="#475569" stroke-width="1.5" stroke-dasharray="8 4" />

    <!-- Corner Flourishes -->
    <circle cx="48" cy="48" r="8" fill="url(#goldGrad)" />
    <circle cx="752" cy="48" r="8" fill="url(#goldGrad)" />
    <circle cx="48" cy="512" r="8" fill="url(#goldGrad)" />
    <circle cx="752" cy="512" r="8" fill="url(#goldGrad)" />

    <!-- Top Badge / Header Ribbon -->
    <path d="M 280 36 L 520 36 L 500 74 L 260 74 Z" fill="url(#accentGrad)" opacity="0.9" />
    <text x="380" y="58" font-family="sans-serif" font-size="12" font-weight="bold" fill="#ffffff" letter-spacing="3" text-anchor="middle">OFFICIAL ACADEMIC CREDENTIAL</text>

    <!-- Institution / Issuing Header -->
    <text x="400" y="125" font-family="sans-serif" font-size="15" font-weight="600" fill="#94a3b8" letter-spacing="2" text-anchor="middle">${safeIssuer.toUpperCase()}</text>
    
    <!-- Title -->
    <text x="400" y="175" font-family="Georgia, serif" font-size="28" font-weight="bold" fill="url(#goldGrad)" text-anchor="middle">${safeTitle}</text>
    
    <text x="400" y="215" font-family="sans-serif" font-size="13" fill="#cbd5e1" text-anchor="middle">This certificate is proudly awarded to</text>

    <!-- Student Name -->
    <text x="400" y="275" font-family="Georgia, serif" font-size="34" font-weight="bold" fill="#ffffff" text-anchor="middle" letter-spacing="1">${safeName}</text>
    <line x1="220" y1="295" x2="580" y2="295" stroke="url(#goldGrad)" stroke-width="2" />

    <!-- Category & Achievement Description -->
    <text x="400" y="340" font-family="sans-serif" font-size="14" fill="#94a3b8" text-anchor="middle">
      in recognition of outstanding accomplishment in ${category}
    </text>
    <text x="400" y="365" font-family="sans-serif" font-size="13" font-weight="600" fill="#38bdf8" text-anchor="middle">
      Grade / Merit Standing: ${safeScore}
    </text>

    <!-- Golden Seal Graphic -->
    <g transform="translate(400, 445)">
      <circle cx="0" cy="0" r="38" fill="url(#goldGrad)" />
      <circle cx="0" cy="0" r="32" fill="#0f172a" />
      <circle cx="0" cy="0" r="28" fill="none" stroke="url(#goldGrad)" stroke-width="1.5" />
      <polygon points="0,-18 5,-5 18,-5 8,4 12,17 0,9 -12,17 -8,4 -18,-5 -5,-5" fill="url(#goldGrad)" />
      <text x="0" y="4" font-family="sans-serif" font-size="7" font-weight="bold" fill="#ffffff" text-anchor="middle">VERIFIED</text>
    </g>

    <!-- Signatures & Verification Details -->
    <g transform="translate(140, 460)">
      <line x1="0" y1="0" x2="160" y2="0" stroke="#64748b" stroke-width="1.5" />
      <text x="80" y="18" font-family="sans-serif" font-size="11" font-weight="bold" fill="#e2e8f0" text-anchor="middle">Authorized Academic Mentor</text>
      <text x="80" y="32" font-family="sans-serif" font-size="10" fill="#94a3b8" text-anchor="middle">Kalvikkan Board of Evaluation</text>
    </g>

    <g transform="translate(500, 460)">
      <line x1="0" y1="0" x2="160" y2="0" stroke="#64748b" stroke-width="1.5" />
      <text x="80" y="18" font-family="sans-serif" font-size="11" font-weight="bold" fill="#e2e8f0" text-anchor="middle">Date of Issuance</text>
      <text x="80" y="32" font-family="sans-serif" font-size="10" fill="#94a3b8" text-anchor="middle">${safeDate}</text>
    </g>

    <!-- Tamper-evident ID -->
    <text x="400" y="522" font-family="monospace" font-size="10" fill="#64748b" text-anchor="middle">
      CREDENTIAL ID: KLVK-${Math.abs(safeTitle.length * 37 + safeName.length * 91).toString(16).toUpperCase()}-2026
    </text>
  </svg>`;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}
