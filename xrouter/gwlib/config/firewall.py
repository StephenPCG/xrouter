from pydantic import BaseModel


class Firewall(BaseModel):
    def apply(self):
        from ..gwlib import gw

        setup_file = gw.bin_root / "setup-firewall.nft"
        gw.print(f"setup file: {setup_file}")
        gw.install_template_file(
            setup_file,
            "firewall.nft",
            dict(),
            mode="755",
        )

        custom_file = gw.config_root / "firewall.nft"
        gw.print(f"custom file: {custom_file}")
        if custom_file.exists():
            gw.print(f"Custom firewall file exists, skip updating: {custom_file}")
            return

        gw.install_template_file(
            custom_file,
            "firewall-custom.nft",
            dict(),
        )
