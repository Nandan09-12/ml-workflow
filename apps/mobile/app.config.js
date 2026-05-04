const appJson = require("./app.json");

module.exports = () => {
  const expoConfig = {
    ...appJson.expo,
    extra: {
      ...(appJson.expo.extra ?? {}),
    },
  };

  const expoOwner = process.env.EXPO_OWNER?.trim();
  const easProjectId = process.env.EAS_PROJECT_ID?.trim();

  if (easProjectId) {
    expoConfig.extra = {
      ...expoConfig.extra,
      eas: {
        ...(expoConfig.extra.eas ?? {}),
        projectId: easProjectId,
      },
    };
  } else if (expoConfig.extra.eas) {
    const { eas, ...restExtra } = expoConfig.extra;
    expoConfig.extra = restExtra;
  }

  if (expoOwner) {
    expoConfig.owner = expoOwner;
  } else {
    delete expoConfig.owner;
  }

  return expoConfig;
};
