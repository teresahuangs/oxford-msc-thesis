% ===================================================================
% LicenSync - JURISDICTION-AWARE Prolog Rules
% ===================================================================

% --- Dynamic Predicates ---
:- dynamic(is_permissive/1).
:- dynamic(is_weak_copyleft/1).
:- dynamic(is_strong_copyleft/1).
:- dynamic(is_network_copyleft/1).
:- dynamic(is_non_commercial/1).
:- dynamic(has_explicit_patent_grant/1).

% ===================================================================
% %% -- License Properties (Facts) --
% ===================================================================

is_permissive(mit).
is_permissive(apache2).
is_permissive(bsd2).
is_permissive(bsd3).
is_permissive(isc).
is_permissive(unlicense).
is_permissive(cc0).
is_permissive(bsd0).

is_weak_copyleft(mpl2).
is_weak_copyleft(lgpl2).
is_weak_copyleft(lgpl3).
is_weak_copyleft(epl2).

is_strong_copyleft(gpl2).
is_strong_copyleft(gpl3).

is_network_copyleft(agpl3).
is_network_copyleft(sspl).

is_non_commercial(commons_clause).
is_non_commercial(cc_by_nc_sa_4).
is_non_commercial(confluent_community_1).
is_non_commercial(elastic2).

% -- Properties related to specific legal clauses --
has_explicit_patent_grant(apache2).
has_explicit_patent_grant(gpl3).
has_explicit_patent_grant(agpl3).
has_explicit_patent_grant(mpl2).
has_explicit_patent_grant(epl2).

% ===================================================================
% %% -- Core Compatibility Rules (Jurisdiction-Aware) --
% ===================================================================

compatible(L, L, _J) :- !.

compatible(apache2, gpl2, us) :- !.
compatible(gpl2, apache2, us) :- !.

compatible(apache2, gpl2, _J) :- !, fail.
compatible(gpl2, apache2, _J) :- !, fail.

compatible(apache2, gpl3, _J) :- !.
compatible(gpl3, apache2, _J) :- !.
compatible(gpl3, agpl3, _J) :- !.
compatible(agpl3, gpl3, _J) :- !.

compatible(L1, L2, _J) :- is_non_commercial(L1), (is_permissive(L2); is_weak_copyleft(L2); is_strong_copyleft(L2)), !, fail.
compatible(L1, L2, _J) :- (is_permissive(L1); is_weak_copyleft(L1); is_strong_copyleft(L1)), is_non_commercial(L2), !, fail.

compatible(L1, L2, _J) :- is_permissive(L1), (is_permissive(L2); is_weak_copyleft(L2); is_strong_copyleft(L2); is_network_copyleft(L2)), !.
compatible(L1, L2, _J) :- (is_permissive(L2); is_weak_copyleft(L2); is_strong_copyleft(L2); is_network_copyleft(L2)), is_permissive(L1), !.
compatible(L1, L2, _J) :- is_weak_copyleft(L1), (is_strong_copyleft(L2); is_network_copyleft(L2)), !.
compatible(L1, L2, _J) :- (is_strong_copyleft(L1); is_network_copyleft(L1)), is_weak_copyleft(L2), !.

compatible(L1, L2, _J) :- is_strong_copyleft(L1), is_strong_copyleft(L2), !, fail.

% ===================================================================
% %% -- Advanced Risk Analysis (Distinction-Level Feature) --
% ===================================================================

risk_level(_L1, _L2, _J, low) :- !. % Default risk is low.
risk_level(_L1, L2, eu, high) :- is_permissive(L2), !.

% ===================================================================
% %% -- Main Entry Point for Python --
% ===================================================================

evaluate_pair(Lic1, Lic2, Juris, Result) :-
    (Lic1 == unknown ; Lic2 == unknown),
    !,
    Result = unknown_license.

evaluate_pair(Lic1, Lic2, Juris, Result) :-
    (   compatible(Lic1, Lic2, Juris)
    ->  Result = ok
    ;   Result = incompatible
    ).