// Prism grammars for the primer languages Prism does not ship. They cover
// comments, strings, keywords, types and numbers: enough to read a primer,
// not a full parser. Keywords come from each language's reference manual.

const words = (list, flags = "") => new RegExp(`\\b(?:${list.split(/\s+/).join("|")})\\b`, flags);

const NUMBER = /\b\d+(?:\.\d+)?\b/;
const STRING = { pattern: /"(?:\\.|[^"\\\n])*"/, greedy: true };
const PUNCTUATION = /[()[\]{},;]/;
const C_COMMENTS = [
  { pattern: /\/\*[\s\S]*?\*\//, greedy: true },
  { pattern: /\/\/.*/, greedy: true },
];
const ML_COMMENT = { pattern: /\(\*[\s\S]*?\*\)/, greedy: true };

const LEAN = {
  comment: [
    { pattern: /\/-[\s\S]*?-\//, greedy: true },
    { pattern: /--.*/, greedy: true },
  ],
  string: STRING,
  attribute: { pattern: /@\[[^\]]*\]/, alias: "attr-name" },
  keyword: words(
    "theorem lemma def abbrev example structure inductive class instance where deriving namespace section end " +
      "open import variable universe set_option by fun let mut in if then else match with do for while return " +
      "have show from calc at termination_by decreasing_by private protected noncomputable partial axiom sorry"
  ),
  builtin: words(
    "simp simp_all omega unfold split induction cases case exact apply intro intros rfl rw constructor all_goals " +
      "any_goals try first repeat decide native_decide mvcgen grind linarith trivial assumption contradiction refine next"
  ),
  "class-name": words("Nat Int List Array Fin Bool Prop Type Id String Option Unit"),
  boolean: words("true false True False"),
  number: NUMBER,
  operator: /[≥≤≠∧∨¬→←↔∀∃λ×∘⟨⟩]|:=|=>|<;>|[<>=+\-*\/|:]/,
  punctuation: PUNCTUATION,
};

const VELVET = {
  ...LEAN,
  keyword: [
    words("method returns require requires ensures invariant decreasing prove_correct"),
    LEAN.keyword,
  ],
  builtin: [words("velvet_vcgen finish loom_solve"), LEAN.builtin],
};

const DAFNY = {
  comment: C_COMMENTS,
  attribute: { pattern: /\{:[^}]*\}/, alias: "attr-name" },
  string: STRING,
  keyword: words(
    "method function predicate lemma ghost returns requires ensures reads modifies decreases invariant assert " +
      "assume var if then else while for forall exists return calc match case class datatype module import const " +
      "new old fresh this null in by opaque reveal twostate static constructor type trait extends print break label"
  ),
  "class-name": words("int nat bool real char string seq set multiset map array object"),
  boolean: words("true false"),
  number: NUMBER,
  operator: /<==>|==>|<==|&&|\|\||::|:=|\.\.|==|!=|<=|>=|[<>+\-*\/%!|]/,
  punctuation: PUNCTUATION,
};

const FSTAR = {
  comment: [ML_COMMENT, { pattern: /\/\/.*/, greedy: true }],
  string: STRING,
  keyword: words(
    "module open let rec in val type and match with fun if then else begin end assert assume admit requires " +
      "ensures decreases returns Lemma Tot GTot Pure ST Stack effect noeq unfold inline_for_extraction private " +
      "friend include forall exists when of calc by introduce eliminate"
  ),
  "class-name": words("int nat pos bool list unit prop Type0 string"),
  boolean: words("true false"),
  number: NUMBER,
  operator: /==>|<==>|->|<-|::|\/\\|\\\/|==|<>|<=|>=|[<>=+\-*\/@|^~]/,
  punctuation: PUNCTUATION,
};

const ISABELLE = {
  comment: ML_COMMENT,
  // Text and comments in cartouches.
  string: { pattern: /‹[^›]*›|\\<open>[\s\S]*?\\<close>/, greedy: true },
  // Before keywords, so that the `and` in \<and> stays part of the symbol.
  symbol: { pattern: /\\<\^?[A-Za-z]+>/, alias: "operator" },
  keyword: words(
    "theory imports begin end fun function primrec definition abbreviation datatype type_synonym lemma theorem " +
      "corollary proof qed by apply done using unfolding assumes shows obtains fixes where and for if then else " +
      "case of let in have show hence thus from with next moreover ultimately also finally sorry oops text " +
      "section subsection locale context"
  ),
  builtin: words(
    "simp simp_all auto blast force fastforce arith linarith induction cases rule metis smt presburger algebra " +
      "eval intro elim subst clarsimp"
  ),
  "class-name": words("int nat bool list set real"),
  boolean: words("True False"),
  number: NUMBER,
  operator: /::|[⇒≥≤∧∨¬∀∃λ=+\-*#@<>|]/,
  punctuation: /[()[\]{},;"]/,
};

const PVS = {
  comment: { pattern: /%.*/, greedy: true },
  string: STRING,
  keyword: words(
    "THEORY BEGIN END IMPORTING LEMMA THEOREM AXIOM CONJECTURE COROLLARY RECURSIVE MEASURE BY IF THEN ELSIF " +
      "ELSE ENDIF LAMBDA FORALL EXISTS LET IN AND OR NOT IMPLIES IFF TYPE VAR CASES OF ENDCASES DATATYPE WITH",
    "i"
  ),
  "class-name": words("nat int real bool posnat rat"),
  boolean: words("TRUE FALSE", "i"),
  number: NUMBER,
  operator: /=>|<=>|\/=|<=|>=|[<>=+\-*\/:]/,
  punctuation: PUNCTUATION,
};

const BOOGIE = {
  comment: C_COMMENTS,
  attribute: { pattern: /\{:[^}]*\}/, alias: "attr-name" },
  string: STRING,
  keyword: words(
    "procedure implementation function axiom var const type requires ensures modifies free returns invariant " +
      "assert assume havoc call if else while goto return break forall exists old where unique complete lambda"
  ),
  "class-name": words("int bool real"),
  boolean: words("true false"),
  number: NUMBER,
  operator: /<==>|==>|&&|\|\||::|:=|==|!=|<=|>=|[<>+\-*\/%!]/,
  punctuation: PUNCTUATION,
};

const VIPER = {
  comment: C_COMMENTS,
  string: STRING,
  keyword: words(
    "field method function predicate domain axiom returns requires ensures invariant var if elseif else while " +
      "assert assume exhale inhale fold unfold unfolding in new old forall exists acc wildcard write none result " +
      "label goto import define perm fresh apply package"
  ),
  "class-name": words("Int Bool Ref Perm Seq Set Multiset Map"),
  boolean: words("true false null"),
  number: NUMBER,
  operator: /<==>|==>|&&|\|\||::|:=|==|!=|<=|>=|[<>+\-*\/%!]/,
  punctuation: PUNCTUATION,
};

const WHYML = {
  comment: ML_COMMENT,
  attribute: { pattern: /\[@[^\]]*\]/, alias: "attr-name" },
  string: STRING,
  keyword: words(
    "module end use import clone theory type function predicate let rec in val ghost lemma axiom goal requires " +
      "ensures returns raises reads writes variant invariant assert assume check if then else match with for to " +
      "downto do done while begin exception raise try forall exists not old at result ref mutable absurd label " +
      "constant scope by so"
  ),
  "class-name": words("int bool unit real list array"),
  boolean: words("true false"),
  number: NUMBER,
  operator: /->|<->|\/\\|\\\/|<-|:=|<>|<=|>=|[<>=+\-*\/!|]/,
  punctuation: PUNCTUATION,
};

export function defineGrammars(Prism) {
  Object.assign(Prism.languages, {
    lean: LEAN,
    velvet: VELVET,
    dafny: DAFNY,
    fstar: FSTAR,
    isabelle: ISABELLE,
    pvs: PVS,
    boogie: BOOGIE,
    viper: VIPER,
    whyml: WHYML,
  });
}
