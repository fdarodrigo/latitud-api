from rest_framework import serializers

class ImovelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Imovel
        fields = ('endereço', 'valor', 'quartos', 'área')