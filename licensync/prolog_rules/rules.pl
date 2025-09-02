% ===================================================================
%
% LicenSync v2.0 - Comprehensive JURISDICTION-AWARE Prolog Rules
% (Corrected and Enhanced Version)
%
% ===================================================================

% --- Dynamic Predicates ---
:- dynamic(is_permissive/1).
:- dynamic(is_weak_copyleft/1).
:- dynamic(is_strong_copyleft/1).
:- dynamic(is_network_copyleft/1).
:- dynamic(is_non_commercial/1).
:- dynamic(is_source_available/1).
:- dynamic(is_public_domain_equivalent/1).
:- dynamic(is_creative_commons/1).
:- dynamic(has_explicit_patent_grant/1).
:- dynamic(has_patent_retaliation/1).
:- dynamic(has_strong_as_is_disclaimer/1).
:- dynamic(requires_source_modification_disclosure/1).
:- dynamic(is_gpl2_only/1).
:- dynamic(allows_sublicensing/1).
% ADDED: Predicate for the new copyright notice facts.
:- dynamic(requires_notice_and_copyright/1).


% ===================================================================
% %% -- Known Jurisdictions --
% ===================================================================
is_jurisdiction(global).
is_jurisdiction(us).
is_jurisdiction(eu).
is_jurisdiction(de).
is_jurisdiction(uk).

% ===================================================================
% %% -- License Properties (Facts) --
% ===================================================================

% --- Permissive Licenses ---
is_permissive(mit).
is_permissive(apache2).
is_permissive(bsd2).
is_permissive(bsd3).
is_permissive(isc).
is_permissive(bsd0).
is_permissive(unlicense).
is_permissive(wtfpl).
is_permissive(artistic2).

% --- Weak Copyleft Licenses ---
is_weak_copyleft(mpl2).
is_weak_copyleft(lgpl2).
is_weak_copyleft(lgpl2_or_later).
is_weak_copyleft(lgpl3).
is_weak_copyleft(lgpl3_or_later).
is_weak_copyleft(epl2).
is_weak_copyleft(cddl1).
is_weak_copyleft(osl3).

% --- Strong Copyleft Licenses ---
is_strong_copyleft(gpl2).
is_strong_copyleft(gpl2_or_later).
is_strong_copyleft(gpl3).
is_strong_copyleft(gpl3_or_later).

% --- Network Copyleft Licenses ---
is_network_copyleft(agpl3).
is_network_copyleft(agpl3_or_later).
is_network_copyleft(sspl1).
is_network_copyleft(rpl1_5).

% --- Non-Commercial / Source-Available Licenses ---
is_non_commercial(commons_clause).
is_non_commercial(cc_by_nc_sa_4).
is_source_available(confluent_community_1).
is_source_available(elastic2).
is_source_available(bsl1_1).

% --- Creative Commons (Code-incompatible) ---
is_creative_commons(cc_by_nc_sa_4).
is_creative_commons(cc_by_sa_4).
is_creative_commons(cc_by_4).

% --- Public Domain Equivalent ---
is_public_domain_equivalent(unlicense).
is_public_domain_equivalent(cc0).
is_public_domain_equivalent(wtfpl).

% --- Specific Legal Clause Properties ---
has_explicit_patent_grant(apache2).
has_explicit_patent_grant(gpl3).
has_explicit_patent_grant(gpl3_or_later).
has_explicit_patent_grant(agpl3).
has_explicit_patent_grant(agpl3_or_later).
has_explicit_patent_grant(lgpl3).
has_explicit_patent_grant(lgpl3_or_later).
has_explicit_patent_grant(mpl2).
has_explicit_patent_grant(epl2).

has_patent_retaliation(apache2).
has_patent_retaliation(gpl3).
has_patent_retaliation(gpl3_or_later).
has_patent_retaliation(mpl2).
has_patent_retaliation(cddl1).

has_strong_as_is_disclaimer(mit).
has_strong_as_is_disclaimer(bsd2).
has_strong_as_is_disclaimer(bsd3).
has_strong_as_is_disclaimer(isc).

requires_source_modification_disclosure(mpl2).
requires_source_modification_disclosure(lgpl2).
requires_source_modification_disclosure(lgpl3).

is_gpl2_only(gpl2).
is_gpl2_only(lgpl2).

allows_sublicensing(apache2).
allows_sublicensing(gpl3_or_later).
allows_sublicensing(agpl3_or_later).

% ADDED: Facts for notice and copyright requirements to fix the "dead rule".
requires_notice_and_copyright(mit).
requires_notice_and_copyright(apache2).
requires_notice_and_copyright(bsd2).
requires_notice_and_copyright(bsd3).
requires_notice_and_copyright(isc).
requires_notice_and_copyright(gpl2).
requires_notice_and_copyright(gpl2_or_later).
requires_notice_and_copyright(gpl3).
requires_notice_and_copyright(gpl3_or_later).
requires_notice_and_copyright(lgpl2).
requires_notice_and_copyright(lgpl2_or_later).
requires_notice_and_copyright(lgpl3).
requires_notice_and_copyright(lgpl3_or_later).
requires_notice_and_copyright(agpl3).
requires_notice_and_copyright(agpl3_or_later).
requires_notice_and_copyright(mpl2).

% ===================================================================
% %% -- Core Compatibility Rules (Jurisdiction-Aware) --
% ===================================================================


% JURISDICTION (DE): Strong "AS IS" disclaimers can conflict with statutory warranty laws.
compatible(L1, L2, de) :- (is_strong_copyleft(L1); is_weak_copyleft(L1)), has_strong_as_is_disclaimer(L2), !, fail.
compatible(L1, L2, de) :- has_strong_as_is_disclaimer(L1), (is_strong_copyleft(L2); is_weak_copyleft(L2)), !, fail.

% --- GLOBAL RULES ---
% A license is always compatible with itself. (Should be the first rule).
compatible(L, L, _J) :- !.

% This is the CORRECT rule for apache2 and gpl2, which are incompatible everywhere.
compatible(apache2, L, _J) :- (L == gpl2; L == gpl2_or_later), !, fail.
compatible(L, apache2, _J) :- (L == gpl2; L == gpl2_or_later), !, fail.

% GPLv2-only licenses are incompatible with GPLv3.
compatible(L1, L2, _J) :- is_gpl2_only(L1), (L2 == gpl3; L2 == gpl3_or_later), !, fail.
compatible(L1, L2, _J) :- (L1 == gpl3; L1 == gpl3_or_later), is_gpl2_only(L2), !, fail.

% Non-commercial/Source-available are incompatible with standard OSS licenses.
compatible(L1, L2, _J) :- (is_non_commercial(L1); is_source_available(L1)), \+ (is_non_commercial(L2); is_source_available(L2)), !, fail.
compatible(L1, L2, _J) :- \+ (is_non_commercial(L1); is_source_available(L1)), (is_non_commercial(L2); is_source_available(L2)), !, fail.

% Most Creative Commons licenses are not suitable for software.
compatible(L1, L2, _J) :- is_creative_commons(L1), \+ is_public_domain_equivalent(L1), !, fail.
compatible(L1, L2, _J) :- is_creative_commons(L2), \+ is_public_domain_equivalent(L2), !, fail.

% Two different strong copyleft licenses are incompatible.
compatible(L1, L2, _J) :- is_strong_copyleft(L1), is_strong_copyleft(L2), L1 \== L2, !, fail.

% Apache-2.0 IS compatible with GPLv3.
compatible(apache2, L, _J) :- (L == gpl3; L == gpl3_or_later), !.
compatible(L, apache2, _J) :- (L == gpl3; L == gpl3_or_later), !.

% GPLv3 family compatibility.
compatible(L1, L2, _J) :- (L1 == gpl3_or_later; L1 == lgpl3_or_later), (L2 == agpl3_or_later), !.
compatible(L1, L2, _J) :- (L1 == agpl3_or_later), (L2 == gpl3_or_later; L2 == lgpl3_or_later), !.

% MPL-2.0 is compatible with GPL/LGPL/AGPL.
compatible(mpl2, L, _J) :- (is_strong_copyleft(L); is_network_copyleft(L); is_weak_copyleft(L)), !.
compatible(L, mpl2, _J) :- (is_strong_copyleft(L); is_network_copyleft(L); is_weak_copyleft(L)), !.

% Permissive licenses are generally compatible with everything except non-commercial.
compatible(L1, L2, _J) :- is_permissive(L1), \+ (is_non_commercial(L2); is_source_available(L2)), !.
compatible(L1, L2, _J) :- is_permissive(L2), \+ (is_non_commercial(L1); is_source_available(L1)), !.

% Weak copyleft is compatible with strong copyleft (under the terms of the strong copyleft license).
compatible(L1, L2, _J) :- is_weak_copyleft(L1), (is_strong_copyleft(L2); is_network_copyleft(L2)), !.
compatible(L1, L2, _J) :- (is_strong_copyleft(L1); is_network_copyleft(L1)), is_weak_copyleft(L2), !.

% ===================================================================
% %% -- Advanced Risk Analysis --
% ===================================================================

risk_level(_L1, L2, eu, high) :- has_strong_as_is_disclaimer(L2), !.
risk_level(_L1, L2, uk, medium) :- has_strong_as_is_disclaimer(L2), !.
risk_level(_L1, L2, de, high) :- is_public_domain_equivalent(L2), !.
risk_level(_L1, L2, _J, medium) :- (L2 == gpl2; L2 == gpl2_or_later), \+ has_explicit_patent_grant(L2), !.
risk_level(L1, L2, _J, business_risk) :- is_permissive(L1), (is_strong_copyleft(L2); is_network_copyleft(L2)), !.
risk_level(L1, L2, _J, business_risk) :- (is_strong_copyleft(L1); is_network_copyleft(L1)), is_permissive(L2), !.
risk_level(_L1, _L2, _J, low).

% ===================================================================
% %% -- Obligation Extractor (Jurisdiction-Aware) --
% REFACTORED: All rules are now obligation/3 to be truly jurisdiction-aware.
% ===================================================================

obligation(L, _J, 'permissive') :- is_permissive(L).
obligation(L, _J, 'weak_copyleft') :- is_weak_copyleft(L).
obligation(L, _J, 'strong_copyleft') :- is_strong_copyleft(L).
obligation(L, _J, 'network_copyleft') :- is_network_copyleft(L).
obligation(L, _J, 'non_commercial_use_only') :- is_non_commercial(L).
obligation(L, _J, 'source_available_restrictions') :- is_source_available(L).
obligation(L, _J, 'explicit_patent_grant') :- has_explicit_patent_grant(L).
obligation(L, _J, 'patent_retaliation_clause') :- has_patent_retaliation(L).
obligation(L, _J, 'requires_source_modification_disclosure') :- requires_source_modification_disclosure(L).
obligation(L, _J, 'allows_sublicensing') :- allows_sublicensing(L).

% This rule is now active because the facts were added above.
obligation(L, _J, 'requires_notice_and_copyright') :- requires_notice_and_copyright(L).

% Jurisdiction-specific obligation for licenses with "AS IS" disclaimers.
obligation(L, eu, 'includes_strong_as_is_disclaimer_(may_be_unenforceable)') :- has_strong_as_is_disclaimer(L).
obligation(L, de, 'includes_strong_as_is_disclaimer_(may_conflict_with_statutory_warranty)') :- has_strong_as_is_disclaimer(L).
% Default rule for other jurisdictions.
obligation(L, J, 'includes_strong_as_is_disclaimer') :-
    has_strong_as_is_disclaimer(L),
    \+ (J == eu), \+ (J == de).

% Specific fact for GPLv2's patent grant status.
obligation(gpl2, _J, 'no_explicit_patent_grant').
obligation(gpl2_or_later, _J, 'no_explicit_patent_grant').

% ===================================================================
% %% -- Main Entry Point for Logic Evaluation --
% ===================================================================

evaluate_pair(Lic1, Lic2, Juris, Result, Risk) :-
    ( is_jurisdiction(Juris) -> J = Juris ; J = global ),
    (Lic1 == unknown ; Lic2 == unknown),
    !,
    Result = unknown_license,
    Risk = undefined.

evaluate_pair(Lic1, Lic2, Juris, Result, Risk) :-
    ( is_jurisdiction(Juris) -> J = Juris ; J = global ),
    (   compatible(Lic1, Lic2, J)
    ->  Result = ok,
        risk_level(Lic1, Lic2, J, Risk)
    ;   Result = incompatible,
        Risk = high
    ).