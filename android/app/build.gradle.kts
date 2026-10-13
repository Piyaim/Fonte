plugins {
    id("com.android.application")
}

val keystorePath: String? = System.getenv("FONTE_KEYSTORE")

android {
    namespace = "app.fonte"
    compileSdk = 34

    defaultConfig {
        applicationId = providers.gradleProperty("APP_ID").get()
        minSdk = 24
        targetSdk = 34
        versionCode = providers.gradleProperty("VERSION_CODE").get().toInt()
        versionName = providers.gradleProperty("VERSION_NAME").get()
    }

    signingConfigs {
        if (keystorePath != null) {
            create("release") {
                storeFile = file(keystorePath)
                storePassword = System.getenv("FONTE_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("FONTE_KEY_ALIAS")
                keyPassword = System.getenv("FONTE_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            // Sans clé fournie (build local, F-Droid qui signe lui-même), la clé de debug sert de repli.
            signingConfig = signingConfigs.findByName("release") ?: signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    lint {
        abortOnError = false
    }

    // L'appli web (dossier server/static) est embarquée telle quelle dans l'APK : une seule source pour les deux versions.
    sourceSets {
        getByName("main") {
            assets.srcDir("../../server/static")
        }
    }
}
