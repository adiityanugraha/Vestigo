import { InferenceSession, Tensor } from "onnxruntime-web";

export async function loadModelSession(modelPath = "/model.onnx") {
  return InferenceSession.create(modelPath, {
    executionProviders: ["wasm"],
  });
}

export async function runModelInference(
  session: InferenceSession,
  features: number[],
  inputName = "input",
) {
  const tensor = new Tensor("float32", Float32Array.from(features), [
    1,
    features.length,
  ]);
  const outputs = await session.run({ [inputName]: tensor });
  const outputName = session.outputNames[0];

  return Array.from(outputs[outputName].data as Float32Array);
}
