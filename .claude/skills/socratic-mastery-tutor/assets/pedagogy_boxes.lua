-- Pandoc Lua filter: turns fenced divs (::: definition {title="..."}) into
--   * tcolorbox environments for LaTeX/PDF
--   * custom-style paragraphs (styled in reference.docx) for DOCX
-- One source, two outputs, so the .tex and .docx cannot drift apart.

local boxes = {
  definition = "Definition",
  keyidea    = "Key idea",
  warning    = "Watch out",
  exercise   = "Exercise",
  create     = "Create",
  term       = "Term",
}

local function first_box_class(el)
  for cls, _ in pairs(boxes) do
    if el.classes:includes(cls) then return cls end
  end
  return nil
end

-- Equation numbering. Write a labelled display equation as
--     $$ ... $$ {#eq:name}
-- and cite it in prose as  @eq:name  -> renders "(n)". Numbers count per document, in order.
-- Pandoc has no built-in equation labels; this keeps .tex and .docx identical without pandoc-crossref.
local eq_number = {}
local eq_count = 0

local function number_equations(p)
  -- A paragraph may hold several labelled display equations (no blank line between them), so scan all of
  -- them. A label counts only when it sits IMMEDIATELY after the display math (optionally after a Space).
  local inl, changed, i = p.content, false, 1
  while i <= #inl do
    local m = inl[i]
    if m.t == "Math" and m.mathtype == "DisplayMath" then
      local j = i + 1
      while j <= #inl and inl[j].t == "Space" do j = j + 1 end
      if j <= #inl and inl[j].t == "Str" then
        local id = inl[j].text:match("^{#(eq:[%w_%-]+)}$")
        if id then
          eq_count = eq_count + 1
          eq_number[id] = eq_count
          m.text = m.text .. " \\qquad (" .. eq_count .. ")"
          for k = j, i + 1, -1 do table.remove(inl, k) end   -- drop the label and the Space before it
          changed = true
        end
      end
    end
    i = i + 1
  end
  if changed then return (p.t == "Plain") and pandoc.Plain(inl) or pandoc.Para(inl) end
  return nil
end

local function resolve_refs(c)
  -- One Cite may group several keys ([@eq:a; @eq:b]); render every one, "(1); (2)", never only the first.
  local parts, any_eq = {}, false
  for _, cit in ipairs(c.citations) do
    local id = cit.id
    if id:match("^eq:") then
      any_eq = true
      local n = eq_number[id]
      table.insert(parts, n and ("(" .. n .. ")") or ("(??" .. id .. ")"))
    else
      table.insert(parts, "@" .. id)
    end
  end
  if any_eq then return pandoc.Str(table.concat(parts, "; ")) end
  return nil
end

local function latex_escape(s)
  local map = { ["\\"] = "\\textbackslash{}", ["&"] = "\\&", ["%"] = "\\%", ["$"] = "\\$", ["#"] = "\\#",
                ["_"] = "\\_", ["{"] = "\\{", ["}"] = "\\}", ["~"] = "\\textasciitilde{}", ["^"] = "\\textasciicircum{}" }
  return (s:gsub("[\\&%%$#_{}~^]", map))
end

local function title_inlines(title)
  -- Parse "a <title>" so a title such as "1. Find v", "- note" or "> quote" stays inline text instead of becoming a
  -- list or block quote (whose block content pandoc.Strong cannot hold); then drop the leading "a" and its space.
  local ok, doc = pcall(pandoc.read, "a " .. title, "markdown")
  if ok and #doc.blocks == 1 and (doc.blocks[1].t == "Para" or doc.blocks[1].t == "Plain") then
    local c = doc.blocks[1].content
    if #c >= 3 and c[1].t == "Str" and c[1].text == "a" and c[2].t == "Space" then
      table.remove(c, 1); table.remove(c, 1)
      return c
    end
  end
  return { pandoc.Str(title) }
end

local function title_latex(inl, title)
  if pandoc.write then   -- pandoc >= 2.17
    local ok, s = pcall(pandoc.write, pandoc.Pandoc({ pandoc.Plain(inl) }), "latex")
    if ok then return (s:gsub("%s+$", "")) end
  end
  return latex_escape(title)
end

function Div(el)
  local cls = first_box_class(el)
  if not cls then return nil end
  local title = el.attributes["title"] or boxes[cls]

  -- The title is Markdown (it may hold $math$, & % _ #): parse it, so LaTeX special characters are escaped
  -- and math is typeset, instead of pasting raw text into \begin{tbox-...}{...}.
  local inl = title_inlines(title)
  if FORMAT:match("latex") then
    return {
      pandoc.RawBlock("latex", "\\begin{tbox-" .. cls .. "}{" .. title_latex(inl, title) .. "}"),
      pandoc.Div(el.content),
      pandoc.RawBlock("latex", "\\end{tbox-" .. cls .. "}"),
    }
  elseif FORMAT:match("docx") then
    local head = pandoc.Para({ pandoc.Strong(inl) })
    local blocks = { head }
    for _, b in ipairs(el.content) do table.insert(blocks, b) end
    return pandoc.Div(blocks, pandoc.Attr("", {}, { ["custom-style"] = "Box-" .. cls }))
  end
  return nil
end

-- Pass 1 numbers every labelled equation; pass 2 resolves @eq: citations and builds the boxes.
return {
  { Para = number_equations, Plain = number_equations },   -- Plain: tight list items and table cells
  { Cite = resolve_refs, Div = Div },
}
