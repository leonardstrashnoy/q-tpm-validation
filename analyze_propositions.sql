-- Q-TPM Proposition Analysis (SQLite compatible)

-- Proposition 1: Non-commutativity
SELECT 
    revisionist,
    ROUND(AVG(curvature), 4) AS avg_curvature,
    COUNT(*) AS n
FROM worldlines
GROUP BY revisionist;

-- Proposition 2: Pathway interference
SELECT 
    (expedient + global) AS interfering_pathways,
    ROUND(AVG(curvature), 4) AS avg_curvature,
    COUNT(*) AS n
FROM worldlines
GROUP BY interfering_pathways
ORDER BY interfering_pathways;

-- Proposition 3: Value-driven stability
SELECT 
    value_driven,
    ROUND(AVG(path_curvature), 5) AS stability,
    ROUND(AVG(local_density), 2) AS avg_density,
    COUNT(*) AS n
FROM worldlines
GROUP BY value_driven;

-- Proposition 4: Global halos in dense environments
SELECT 
    global,
    ROUND(AVG(local_density), 2) AS mean_density,
    ROUND(MAX(local_density), 2) AS max_density,
    COUNT(*) AS n
FROM worldlines
GROUP BY global;

-- Proposition 5: Analytical + Ruling-guide interaction
SELECT 
    analytical,
    ruling_guide,
    COUNT(*) AS count,
    ROUND(AVG(star_fraction), 3) AS avg_stellar_yield,
    ROUND(AVG(curvature), 4) AS avg_curvature
FROM worldlines
GROUP BY analytical, ruling_guide
ORDER BY count DESC;