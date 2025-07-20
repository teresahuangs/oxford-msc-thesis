license(mit, [
    type("permissive"),
    requires_disclosure(false),
    requires_notice(true),
    restricts_field_of_use("none"),
    jurisdiction_binding("global"),
    provenance_required(false),
    noncommercial_only(false)
]).

license(gpl3, [
    type("copyleft"),
    requires_disclosure(true),
    requires_notice(true),
    restricts_field_of_use("none"),
    jurisdiction_binding("global"),
    provenance_required(true),
    noncommercial_only(false)
]).

license(llama_nc, [
    type("restrictive"),
    requires_disclosure(false),
    requires_notice(true),
    restricts_field_of_use("commercial"),
    jurisdiction_binding("us"),
    provenance_required(true),
    noncommercial_only(true)
]).

license(openrail, [
    type("restrictive"),
    requires_disclosure(false),
    requires_notice(true),
    restricts_field_of_use("military"),
    jurisdiction_binding("global"),
    provenance_required(true),
    noncommercial_only(false)
]).

license(apache2, [
    type("permissive"),
    requires_disclosure(false),
    requires_notice(true),
    restricts_field_of_use("none"),
    jurisdiction_binding("global"),
    provenance_required(false),
    noncommercial_only(false)
]).


license_fallback(mit, permissive).
license_fallback(gpl3, copyleft).
license_fallback(apache2, permissive).
license_fallback(sspl, restrictive).

jurisdiction(global).
jurisdiction(us).

type(L, Type) :-
    license(L, Props),
    member(type(Type), Props).

type(L, Type) :-
    license_fallback(L, Type).


requires_source_disclosure(L, Jurisdiction) :-
    type(L, copyleft),
    Jurisdiction = eu.

incompatible(L1, L2) :-
    type(L1, copyleft),
    type(L2, restrictive),
    L1 \= L2.

compatible(L1, L2) :-
    type(L1, permissive),
    type(L2, permissive).

compatible(L1, L2) :-
    type(L1, permissive),
    type(L2, copyleft).

evaluate_pair(L1, L2, Jurisdiction, Result) :-
    incompatible(L1, L2),
    Result = 'Incompatible under all jurisdictions'.

evaluate_pair(L1, L2, Jurisdiction, Result) :-
    requires_source_disclosure(L2, Jurisdiction),
    format(atom(Result), "~w requires source disclosure under ~w law", [L2, Jurisdiction]).

evaluate_pair(L1, L2, _, Result) :-
    compatible(L1, L2),
    format(atom(Result), "~w and ~w are compatible", [L1, L2]).

evaluate_pair(_, _, _, "Compatibility cannot be determined.").
