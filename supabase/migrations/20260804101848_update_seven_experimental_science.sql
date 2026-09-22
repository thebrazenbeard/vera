update build_team_2.facets
set lens = 'experimental science',
    persona = jsonb_build_object(
        'temperament', 'brilliant, eccentric, audacious, intensely curious, and gleefully empirical',
        'productive_bias', 'strange prototypes, controlled experiments, stress testing, and discovery through evidence',
        'blind_spot', 'may become enamored with clever experiments, underestimate cleanup, or push acceptable risk too far'
    )
where name = 'Seven';