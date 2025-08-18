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
:- dynamic(has_strong_as_is_disclaimer/1).
:- dynamic(is_public_domain_equivalent/1).

% ===================================================================
% %% -- Known Jurisdictions --
% Defines the legal jurisdictions this system models.
% ===================================================================
is_jurisdiction(global).
is_jurisdiction(us).
is_jurisdiction(eu).
is_jurisdiction(de). % Germany

% ===================================================================
% %% -- License Properties (Facts) --
% ===================================================================

is_permissive(mit).
is_permissive(apache2).
is_permissive(bsd2).
is_permissive(bsd3).
is_permissive(isc).
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

has_strong_as_is_disclaimer(mit).
has_strong_as_is_disclaimer(bsd2).
has_strong_as_is_disclaimer(bsd3).
has_strong_as_is_disclaimer(isc).

is_public_domain_equivalent(unlicense).
is_public_domain_equivalent(cc0).

% ===================================================================
% %% -- Core Compatibility Rules (Jurisdiction-Aware) --
% ===================================================================

% --- JURISDICTION-SPECIFIC RULES ---

% JURISDICTION (US): Model stronger implied patent grant in US law for GPLv2.
compatible(apache2, gpl2, us) :- !.
compatible(gpl2, apache2, us) :- !.

% JURISDICTION (DE): In Germany, strong "AS IS" disclaimers can conflict with
% statutory warranty laws, making some combinations legally incompatible.
compatible(L1, L2, de) :-
    (is_strong_copyleft(L1); is_weak_copyleft(L1)),
    has_strong_as_is_disclaimer(L2),
    !, fail.

% --- GLOBAL RULES (Fallback) ---

compatible(L, L, _J) :- !.

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
% %% -- Advanced Risk Analysis (Jurisdiction-Aware) --
% ===================================================================

% JURISDICTION (EU): In the EU, "AS IS" disclaimers in permissive licenses
% may not be fully enforceable under consumer protection laws, creating higher risk.
risk_level(_L1, L2, eu, high) :- is_permissive(L2), !.

% JURISDICTION (DE): In Germany, an authors "moral rights" are very strong.
% Public domain dedications might be legally contested, creating risk.
risk_level(_L1, L2, de, high) :- is_public_domain_equivalent(L2), !.

% Default risk is low for all other cases.
risk_level(_L1, _L2, _J, low).

% ===================================================================
% %% -- Main Entry Point for Python --
% ===================================================================

evaluate_pair(Lic1, Lic2, Juris, Result) :-
    % Ensure the jurisdiction is known, otherwise default to global
    ( is_jurisdiction(Juris) -> J = Juris ; J = global ),
    (Lic1 == unknown ; Lic2 == unknown),
    !,
    Result = unknown_license.

evaluate_pair(Lic1, Lic2, Juris, Result) :-
    ( is_jurisdiction(Juris) -> J = Juris ; J = global ),
    (   compatible(Lic1, Lic2, J)
    ->  Result = ok
    ;   Result = incompatible
    ).