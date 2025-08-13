/**
 * Minimal ORT rules: flag strong copyleft children under permissive parents.
 * This is illustrative; adapt to your policy.
 */
val permissive = setOf("MIT","BSD-2-Clause","BSD-3-Clause","Apache-2.0","ISC","Zlib","Unlicense")
val strongCopyleft = setOf("GPL-2.0-only","GPL-3.0-only","AGPL-3.0-only","GPL-2.0-or-later","GPL-3.0-or-later","AGPL-3.0-or-later")

violation(
    message = "Strong copyleft under permissive parent",
    howToFix = "Consider replacing or isolating the dependency.",
    severity = Severity.ERROR
) {
    isDependency()
    // NOTE: ORT provides license findings per component; this simplified rule
    // checks effective license in the dependency tree.
    require {
        // Parent is project; child is a dependency
        val parentOK = project.id.type != "" // project node exists
        parentOK
    }
    // Component-level conditions; evaluator context exposes license choices
    condition {
        val parentLicenses = project.licenses.map { it.id } // SPDX IDs
        val depLicenses = pkg.licenses.map { it.id }
        (parentLicenses.any { it in permissive } && depLicenses.any { it in strongCopyleft })
    }
}
