const session = await ai.languageModel.create();

// Prompt the model and wait for the whole result to come back.
const result = await session.prompt("Translate to english, only one answer, json format, no explanation needed : Eu era apenas um trabalhdor qualquer de colarinho branco");
console.log(result);
