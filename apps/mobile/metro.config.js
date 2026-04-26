const { getDefaultConfig } = require("expo/metro-config");

const projectRoot = __dirname;
const config = getDefaultConfig(projectRoot);
const reactEntryPoints = new Map([
  ["react", require.resolve("react", { paths: [projectRoot] })],
  ["react/jsx-runtime", require.resolve("react/jsx-runtime", { paths: [projectRoot] })],
  ["react/jsx-dev-runtime", require.resolve("react/jsx-dev-runtime", { paths: [projectRoot] })],
]);

config.resolver.resolveRequest = (context, moduleName, platform) => {
  const redirected = reactEntryPoints.get(moduleName);
  return context.resolveRequest(context, redirected ?? moduleName, platform);
};

module.exports = config;
