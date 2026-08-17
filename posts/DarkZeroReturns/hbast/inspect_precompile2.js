const Handlebars = require('handlebars');

const ast = Handlebars.parse('{{lookup this 1}}');
ast.body[0].params[1].value = "999";  // string, not number
console.log(Handlebars.precompile(ast));
