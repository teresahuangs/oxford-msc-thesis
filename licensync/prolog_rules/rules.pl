% Declare dynamic predicates
:- dynamic license/2.
:- dynamic jurisdiction/1.
:- dynamic jurisdiction_obligation/3.

% -----------------------------------------------------------------------------
% SPDX License Definitions (core attributes)
% -----------------------------------------------------------------------------

license(mit, [
    type(permissive),
    requires_disclosure(false),
    requires_notice(true),
    restricts_field_of_use(none),
    provenance_required(false),
    noncommercial_only(false)
]).

license(apache2, [
    type(permissive),
    requires_disclosure(false),
    requires_notice(true),
    restricts_field_of_use(none),
    provenance_required(false),
    noncommercial_only(false)
]).

license(gpl3, [
    type(copyleft),
    requires_disclosure(true),
    requires_notice(true),
    restricts_field_of_use(none),
    provenance_required(true),
    noncommercial_only(false)
]).

license(sspl, [
    type(restrictive),
    requires_disclosure(true),
    requires_notice(true),
    restricts_field_of_use(cloud_services),
    provenance_required(true),
    noncommercial_only(false)
]).

license(llama_nc, [
    type(restrictive),
    requires_disclosure(false),
    requires_notice(true),
    restricts_field_of_use(commercial),
    provenance_required(true),
    noncommercial_only(true)
]).

license(openrail, [
    type(restrictive),
    requires_disclosure(false),
    requires_notice(true),
    restricts_field_of_use(military),
    provenance_required(true),
    noncommercial_only(false)
]).

% -----------------------------------------------------------------------------
% Jurisdictions
% -----------------------------------------------------------------------------

jurisdiction(global).
jurisdiction(us).
jurisdiction(eu).
jurisdiction(cn).

% -----------------------------------------------------------------------------
% Jurisdiction-specific overrides
% -----------------------------------------------------------------------------

% Format: jurisdiction_obligation(+Jurisdiction, +Obligation, +Value).

jurisdiction_obligation(global, noncommercial_only, enforce_if_money_given).
jurisdiction_obligation(us, noncommercial_only, enforce_if_sold).
jurisdiction_obligation(eu, provenance_required, true).
jurisdiction_obligation(cn, provenance_required, true).

% -----------------------------------------------------------------------------
% Expression evaluation (support SPDX-style "AND", "OR")
% -----------------------------------------------------------------------------

evaluate_expression(License, Jurisdiction, Result) :-
    atom(License),
    evaluate_license(License, Jurisdiction, Result).

evaluate_expression((L1 ; L2), Jurisdiction, Result) :-
    (evaluate_expression(L1, Jurisdiction, ok);
     evaluate_expression(L2, Jurisdiction, ok)),
    Result = ok.

evaluate_expression((L1 , L2), Jurisdiction, Result) :-
    evaluate_expression(L1, Jurisdiction, ok),
    evaluate_expression(L2, Jurisdiction, ok),
    Result = ok.

evaluate_expression(_, _, Result) :-
    Result = 'Incompatible or unsupported expression'.

% -----------------------------------------------------------------------------
% Compatibility rules
% -----------------------------------------------------------------------------

evaluate_license(L, _, unknown_license) :-
    \+ license(L, _).

evaluate_license(L, Jurisdiction, ok) :-
    license(L, _),
    license_compatible(L, Jurisdiction).

license_compatible(L, Jurisdiction) :-
    license(L, Props),
    \+ ( member(noncommercial_only(true), Props),
         jurisdiction_obligation(Jurisdiction, noncommercial_only, enforce_if_sold) ).

% -----------------------------------------------------------------------------
% Obligation queries
% -----------------------------------------------------------------------------

requires_provenance(L, Jurisdiction) :-
    license(L, Props),
    ( member(provenance_required(true), Props)
    ; jurisdiction_obligation(Jurisdiction, provenance_required, true) ).

restricts_commercial_use(L) :-
    license(L, Props),
    member(noncommercial_only(true), Props).

% -----------------------------------------------------------------------------
% Compatibility Explanation
% -----------------------------------------------------------------------------

compatibility_explanation(L, Jurisdiction, Explanation) :-
    evaluate_license(L, Jurisdiction, ok),
    format(atom(Explanation), "~w is compatible under ~w", [L, Jurisdiction]).

compatibility_explanation(L, Jurisdiction, Explanation) :-
    restricts_commercial_use(L),
    jurisdiction_obligation(Jurisdiction, noncommercial_only, enforce_if_sold),
    format(atom(Explanation), "~w restricts commercial use under ~w law", [L, Jurisdiction]).

compatibility_explanation(_, _, 'Compatibility could not be determined.').

% --------------------------------------------------------------------------
%  Helper: get a property value with a fallback
% --------------------------------------------------------------------------
license_prop_or_default(Lic, PropName, Default, Value) :-
    license(Lic, Props),
    (   member(PropTerm, Props),
        PropTerm =.. [PropName, Value]
    ->  true
    ;   Value = Default).

% --------------------------------------------------------------------------
%  Obligation summary  (deterministic, no endless back-tracking)
% --------------------------------------------------------------------------
evaluate_license_obligations(Lic, Jur, ObligList) :-
    license(Lic, _),                 % fail fast if unknown licence
    % basic props
    license_prop_or_default(Lic, requires_notice,     false,  Notice),
    license_prop_or_default(Lic, requires_disclosure, false,  Disclosure),
    license_prop_or_default(Lic, restricts_field_of_use, none, Field),

    % provenance (jurisdiction-aware)
    (requires_provenance(Lic, Jur) -> Prov = true ; Prov = false),

    % non-commercial (jurisdiction-aware)
    (interpreted_noncommercial(Lic, Jur, true) -> NC = true ; NC = false),

    ObligList = [
        requires_notice(Notice),
        requires_disclosure(Disclosure),
        provenance_required(Prov),
        noncommercial_only(NC),
        restricts_field_of_use(Field)
    ], !.     % cut – make the predicate deterministic

% --------------------------------------------------------------------------
%  Determine whether the non-commercial clause is enforced in a jurisdiction
% --------------------------------------------------------------------------

% Global: always enforce if the licence itself is non-commercial
interpreted_noncommercial(Lic, global, true) :-
    license(Lic, Props),
    member(noncommercial_only(true), Props), !.

% US: only enforce if NC=true *and* jurisdiction overrides say “enforce_if_sold”
interpreted_noncommercial(Lic, us, true) :-
    license(Lic, Props),
    member(noncommercial_only(true), Props),
    jurisdiction_obligation(us, noncommercial_only, enforce_if_sold), !.

% Other cases → false
interpreted_noncommercial(_, _, false).
