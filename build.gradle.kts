plugins {
    alias(libs.plugins.kotlin.multiplatform) apply false
    alias(libs.plugins.kotlin.serialization) apply false
}

val aiVersion = providers.gradleProperty("aiVersion").get()
val netonVersion = providers.gradleProperty("netonVersion").get()
require(aiVersion != netonVersion) { "AI and Framework have independent version lines" }

subprojects {
    repositories { mavenCentral() }
    group = "com.netonstream"
    version = aiVersion
    plugins.withId("org.jetbrains.kotlin.multiplatform") {
        if (path == ":neton-ai") {
            extensions.configure<org.jetbrains.kotlin.gradle.dsl.KotlinBaseExtension> {
                @OptIn(org.jetbrains.kotlin.gradle.dsl.abi.ExperimentalAbiValidation::class)
                abiValidation { keepLocallyUnsupportedTargets.set(false) }
            }
        }
        if (org.gradle.internal.os.OperatingSystem.current().isMacOsX) {
            val sdk = providers.exec { commandLine("xcrun", "--sdk", "macosx", "--show-sdk-path") }
                .standardOutput.asText.get().trim()
            extensions.configure<org.jetbrains.kotlin.gradle.dsl.KotlinMultiplatformExtension> {
                targets.withType(org.jetbrains.kotlin.gradle.plugin.mpp.KotlinNativeTarget::class.java).configureEach {
                    if (konanTarget.family.isAppleFamily) binaries.all { linkerOpts("-L$sdk/usr/lib/swift") }
                }
            }
        }
    }
}

project(":neton-ai") {
    apply(plugin = "maven-publish")
    apply(plugin = "signing")
    extensions.configure<org.gradle.api.publish.PublishingExtension> {
        publications.withType<MavenPublication>().configureEach {
            pom {
                name.set("Neton AI")
                description.set("Optional AI integration for Neton with an independent release lifecycle")
                url.set("https://github.com/netonframework/neton-ai")
                licenses { license { name.set("Apache-2.0"); url.set("https://www.apache.org/licenses/LICENSE-2.0.txt") } }
                developers { developer { name.set("Neton Framework"); organization.set("Neton Framework"); organizationUrl.set("https://netonframework.github.io") } }
                scm {
                    url.set("https://github.com/netonframework/neton-ai")
                    connection.set("scm:git:https://github.com/netonframework/neton-ai.git")
                    developerConnection.set("scm:git:ssh://git@github.com/netonframework/neton-ai.git")
                }
            }
        }
        repositories {
            maven { name = "stagingLocal"; url = rootProject.layout.buildDirectory.dir("staging-repo").get().asFile.toURI() }
        }
    }
    afterEvaluate {
        val key = providers.environmentVariable("SIGNING_KEY").orNull
        if (!key.isNullOrBlank()) extensions.configure<org.gradle.plugins.signing.SigningExtension> {
            useInMemoryPgpKeys(key, providers.environmentVariable("SIGNING_PASSWORD").orNull ?: "")
            sign(extensions.getByType<org.gradle.api.publish.PublishingExtension>().publications)
        }
    }
}
