% SPDX license types
license(mit, permissive).
license(gpl3, copyleft).
license(apache2, permissive).
license(sspl, restrictive).

% Jurisdictional overrides
jurisdiction(eu).
jurisdiction(us).

% Example interpretation rules
requires_source_disclosure(License, Jurisdiction) :-
    license(License, copyleft),
    Jurisdiction = eu.

incompatible(L1, L2) :-
    license(L1, copyleft),
    license(L2, restrictive),
    L1 \= L2.

compatible(L1, L2) :-
    license(L1, permissive),
    license(L2, permissive).

compatible(L1, L2) :-
    license(L1, permissive),
    license(L2, copyleft).

evaluate_pair(L1, L2, Jurisdiction, Result) :-
    incompatible(L1, L2),
    Result = 'Incompatible under all jurisdictions'.

evaluate_pair(L1, L2, Jurisdiction, Result) :-
    requires_source_disclosure(L2, Jurisdiction),
    Result = 'Requires source disclosure in this jurisdiction'.

evaluate_pair(L1, L2, _, Result) :-
    compatible(L1, L2),
    Result = 'Compatible'.

evaluate_pair(_, _, _, Result) :-
    Result = 'Undetermined'.
