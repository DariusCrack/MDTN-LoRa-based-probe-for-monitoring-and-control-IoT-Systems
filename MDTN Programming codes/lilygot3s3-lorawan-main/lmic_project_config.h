#define hal_init LMICHAL_init
// project-specific definitions

// S3
#define CFG_esp32_s3 1

#define CFG_eu868 1
//#define CFG_us915 1
//#define CFG_au915 1
//#define CFG_as923 1
// #define LMIC_COUNTRY_CODE LMIC_COUNTRY_CODE_JP      /* for as923-JP; also define CFG_as923 */
//#define CFG_kr920 1
//#define CFG_in866 1
#define CFG_sx1276_radio 1
//#define LMIC_USE_INTERRUPTS

#define LMIC_LORAWAN_SPEC_VERSION    LMIC_LORAWAN_SPEC_VERSION_1_0_3
#define DISABLE_PING
#define DISABLE_BEACONS

#define LMIC_ENABLE_DeviceTimeReq  0


